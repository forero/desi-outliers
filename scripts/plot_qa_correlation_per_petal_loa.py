import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt
from scipy import stats

ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
QA_FILE  = "/global/cfs/cdirs/desicollab/users/rongpu/redshift_qa/new/kibo/per_fiber_qa_stats.fits"

TARGETS = {
    "LRG": {"program": "dark",   "qa_frac": "lrg_frac_fail",       "qa_err": "lrg_frac_fail_err"},
    "BGS": {"program": "bright", "qa_frac": "bgs_bright_frac_fail", "qa_err": "bgs_bright_frac_fail_err"},
}

print("Reading QA file...")
qa_data = fitsio.read(QA_FILE, ext=1)
qa = pd.DataFrame({
    "FIBER":    qa_data["FIBER"].byteswap().newbyteorder(),
    "lrg_frac_fail":            qa_data["lrg_frac_fail"].byteswap().newbyteorder(),
    "lrg_frac_fail_err":        qa_data["lrg_frac_fail_err"].byteswap().newbyteorder(),
    "bgs_bright_frac_fail":     qa_data["bgs_bright_frac_fail"].byteswap().newbyteorder(),
    "bgs_bright_frac_fail_err": qa_data["bgs_bright_frac_fail_err"].byteswap().newbyteorder(),
}).sort_values("FIBER").reset_index(drop=True)

print("Reading zcatalog...")
data = fitsio.read(ZCAT, ext="ZCATALOG", columns=["TARGETID", "TILEID", "PROGRAM", "FIBER"])
df_zcat = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().newbyteorder(),
    "TILEID":   data["TILEID"].byteswap().newbyteorder(),
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
    "FIBER":    data["FIBER"].byteswap().newbyteorder(),
})
print(f"  {len(df_zcat):,} total targets")

print("Reading outliers...")
outliers = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(outliers["TARGETID"], outliers["TILEID"]))
df_zcat["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df_zcat["TARGETID"], df_zcat["TILEID"])
]

fibers = np.arange(5000)

for name, cfg in TARGETS.items():
    program = cfg["program"]
    sub = df_zcat[df_zcat["PROGRAM"] == program]

    n_total   = sub.groupby("FIBER").size().reindex(fibers, fill_value=0).values
    n_outlier = sub[sub["is_outlier"]].groupby("FIBER").size().reindex(fibers, fill_value=0).values
    frac_out  = np.where(n_total > 0, n_outlier / n_total, np.nan)
    err_out   = np.where(n_total > 0, np.sqrt(n_outlier) / n_total, np.nan)

    qa_frac = qa[cfg["qa_frac"]].values.copy()
    qa_err  = qa[cfg["qa_err"]].values.copy()
    qa_frac[qa_frac < 0] = np.nan
    qa_err[qa_err < 0]   = np.nan
    log_qa_frac = np.log10(np.where(qa_frac > 0, qa_frac, np.nan))

    fig, axes = plt.subplots(2, 5, figsize=(18, 8), sharex=False, sharey=True)

    for petal, ax in enumerate(axes.flat):
        sl = slice(petal * 500, (petal + 1) * 500)
        x = log_qa_frac[sl]
        y = frac_out[sl]
        ye = err_out[sl]

        valid = np.isfinite(x) & np.isfinite(y)
        ax.errorbar(x, y, yerr=ye, fmt="o", ms=3, lw=0.5, capsize=0, alpha=0.5)

        if valid.sum() > 2:
            x_v, y_v = x[valid], y[valid]
            pearson_r,  pearson_p  = stats.pearsonr(x_v, y_v)
            spearman_r, spearman_p = stats.spearmanr(x_v, y_v)
            slope, intercept, *_   = stats.linregress(x_v, y_v)
            x_line = np.linspace(x_v.min(), x_v.max(), 100)
            ax.plot(x_line, slope * x_line + intercept, color="k", lw=1.2)
            label = (f"r={pearson_r:.2f}\nρ={spearman_r:.2f}")
            ax.text(0.05, 0.95, label, transform=ax.transAxes, va="top",
                    fontsize=8, family="monospace",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))

        ax.set_title(f"Petal {petal}")
        ax.set_xlabel("log10(QA fail rate)")

    for ax in axes[:, 0]:
        ax.set_ylabel("Outlier fraction")

    fig.suptitle(f"Loa {name} — outlier fraction vs QA failure rate per petal")
    fig.tight_layout()

    outpath = f"plots/qa_correlation_per_petal_{name.lower()}_loa.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
