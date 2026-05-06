import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt
from scipy import stats

ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv"
QA_FILE  = "/global/cfs/cdirs/desicollab/users/rongpu/redshift_qa/new/kibo/per_fiber_qa_stats.fits"

TARGETS = {
    "LRG": {"program": "dark",   "qa_frac": "lrg_frac_fail",        "qa_err": "lrg_frac_fail_err"},
    "BGS": {"program": "bright", "qa_frac": "bgs_bright_frac_fail",  "qa_err": "bgs_bright_frac_fail_err"},
}

print("Reading QA file...")
qa_data = fitsio.read(QA_FILE, ext=1)
qa = pd.DataFrame({
    "FIBER":    qa_data["FIBER"].byteswap().newbyteorder(),
    "lrg_frac_fail":       qa_data["lrg_frac_fail"].byteswap().newbyteorder(),
    "lrg_frac_fail_err":   qa_data["lrg_frac_fail_err"].byteswap().newbyteorder(),
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
xticks = np.arange(0, 5001, 500)

for name, cfg in TARGETS.items():
    program = cfg["program"]
    sub = df_zcat[df_zcat["PROGRAM"] == program]

    n_total   = sub.groupby("FIBER").size().reindex(fibers, fill_value=0)
    n_outlier = sub[sub["is_outlier"]].groupby("FIBER").size().reindex(fibers, fill_value=0)
    frac_out  = np.where(n_total > 0, n_outlier / n_total, np.nan)
    err_out   = np.where(n_total > 0, np.sqrt(n_outlier) / n_total, np.nan)

    qa_frac = qa[cfg["qa_frac"]].values.copy()
    qa_err  = qa[cfg["qa_err"]].values.copy()
    mask = qa_frac < 0
    qa_frac[mask] = np.nan
    qa_err[mask]  = np.nan

    fig, axes = plt.subplots(3, 1, figsize=(12, 11))

    ax = axes[0]
    ax.errorbar(fibers, frac_out, yerr=err_out, fmt="o", ms=2, lw=0.5, capsize=0, alpha=0.6)
    ax.set_ylabel("Outlier fraction")
    ax.set_title(f"{name} — UMAP outlier fraction per fiber")
    ax.set_xticks(xticks)
    ax.grid(axis="x", linewidth=0.8)

    log_qa_frac = np.log10(np.where(qa_frac > 0, qa_frac, np.nan))

    ax = axes[1]
    ax.scatter(fibers, log_qa_frac, s=4, alpha=0.6, color="C1")
    ax.set_ylabel("log10(QA failure rate)")
    ax.set_title(f"{name} — QA failure rate per fiber")
    ax.set_xlabel("Fiber ID")
    ax.set_xticks(xticks)
    ax.grid(axis="x", linewidth=0.8)

    # correlation on valid (non-NaN) pairs
    valid = np.isfinite(log_qa_frac) & np.isfinite(frac_out)
    x_v, y_v = log_qa_frac[valid], frac_out[valid]
    pearson_r, pearson_p   = stats.pearsonr(x_v, y_v)
    spearman_r, spearman_p = stats.spearmanr(x_v, y_v)

    # linear regression for trend line
    slope, intercept, *_ = stats.linregress(x_v, y_v)
    x_line = np.linspace(x_v.min(), x_v.max(), 200)

    ax = axes[2]
    ax.errorbar(log_qa_frac, frac_out, yerr=err_out,
                fmt="o", ms=3, lw=0.5, capsize=0, alpha=0.5, color="C2")
    ax.plot(x_line, slope * x_line + intercept, color="k", lw=1.5, label="linear fit")
    label = (f"Pearson r={pearson_r:.2f} (p={pearson_p:.2e})\n"
             f"Spearman ρ={spearman_r:.2f} (p={spearman_p:.2e})")
    ax.text(0.03, 0.95, label, transform=ax.transAxes, va="top",
            fontsize=9, family="monospace",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))
    ax.set_xlabel("log10(QA failure rate)")
    ax.set_ylabel("Outlier fraction")
    ax.set_title(f"{name} — outlier fraction vs QA failure rate (per fiber)")
    ax.legend()

    fig.suptitle(f"Loa {name} — outlier fraction vs QA failure rate per fiber")
    fig.tight_layout()

    outpath = f"plots/outlier_fraction_vs_qa_per_fiber_{name.lower()}_loa.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
