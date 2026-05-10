"""
Outlier fraction vs QA failure rate for Loa (LRG and BGS).
Produces:
  - outlier_fraction_vs_qa_per_fiber_{lrg,bgs}_loa.png  (3-panel per-fiber)
  - qa_correlation_per_petal_{lrg,bgs}_loa.png           (2×5 per-petal scatter)
"""
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
qa_raw = fitsio.read(QA_FILE, ext=1)
qa = pd.DataFrame({
    "FIBER":                    qa_raw["FIBER"].byteswap().view(qa_raw["FIBER"].dtype.newbyteorder()),
    "lrg_frac_fail":            qa_raw["lrg_frac_fail"].byteswap().view(qa_raw["lrg_frac_fail"].dtype.newbyteorder()),
    "lrg_frac_fail_err":        qa_raw["lrg_frac_fail_err"].byteswap().view(qa_raw["lrg_frac_fail_err"].dtype.newbyteorder()),
    "bgs_bright_frac_fail":     qa_raw["bgs_bright_frac_fail"].byteswap().view(qa_raw["bgs_bright_frac_fail"].dtype.newbyteorder()),
    "bgs_bright_frac_fail_err": qa_raw["bgs_bright_frac_fail_err"].byteswap().view(qa_raw["bgs_bright_frac_fail_err"].dtype.newbyteorder()),
}).sort_values("FIBER").reset_index(drop=True)

print("Reading zcatalog...")
raw = fitsio.read(ZCAT, ext="ZCATALOG", columns=["TARGETID", "TILEID", "PROGRAM", "FIBER"])
df = pd.DataFrame({
    "TARGETID": raw["TARGETID"].byteswap().view(raw["TARGETID"].dtype.newbyteorder()),
    "TILEID":   raw["TILEID"].byteswap().view(raw["TILEID"].dtype.newbyteorder()),
    "PROGRAM":  [p.strip() for p in raw["PROGRAM"]],
    "FIBER":    raw["FIBER"].byteswap().view(raw["FIBER"].dtype.newbyteorder()),
})
print(f"  {len(df):,} targets")

print("Reading outliers...")
out = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(out["TARGETID"], out["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]

fibers   = np.arange(5000)
xticks   = np.arange(0, 5001, 500)

for name, cfg in TARGETS.items():
    program = cfg["program"]
    sub     = df[df["PROGRAM"] == program]

    n_total   = sub.groupby("FIBER").size().reindex(fibers, fill_value=0).values
    n_outlier = sub[sub["is_outlier"]].groupby("FIBER").size().reindex(fibers, fill_value=0).values
    frac_out  = np.where(n_total > 0, n_outlier / n_total, np.nan)
    err_out   = np.where(n_total > 0, np.sqrt(n_outlier) / n_total, np.nan)

    qa_frac = qa[cfg["qa_frac"]].values.copy()
    qa_err  = qa[cfg["qa_err"]].values.copy()
    qa_frac[qa_frac < 0] = np.nan
    qa_err[qa_err < 0]   = np.nan
    log_qa_frac = np.log10(np.where(qa_frac > 0, qa_frac, np.nan))

    # ── per-fiber 3-panel plot ────────────────────────────────────────────────
    valid = np.isfinite(log_qa_frac) & np.isfinite(frac_out)
    x_v, y_v = log_qa_frac[valid], frac_out[valid]
    pearson_r,  pearson_p  = stats.pearsonr(x_v, y_v)
    spearman_r, spearman_p = stats.spearmanr(x_v, y_v)
    slope, intercept, *_   = stats.linregress(x_v, y_v)
    x_line = np.linspace(x_v.min(), x_v.max(), 200)

    fig, axes = plt.subplots(3, 1, figsize=(12, 11))
    axes[0].errorbar(fibers, frac_out, yerr=err_out, fmt="o", ms=2, lw=0.5, capsize=0, alpha=0.6)
    axes[0].set_ylabel("Outlier fraction")
    axes[0].set_title(f"{name} — UMAP outlier fraction per fiber")
    axes[0].set_xticks(xticks); axes[0].grid(axis="x", linewidth=0.8)

    axes[1].scatter(fibers, log_qa_frac, s=4, alpha=0.6, color="C1")
    axes[1].set_ylabel("log10(QA failure rate)")
    axes[1].set_title(f"{name} — QA failure rate per fiber")
    axes[1].set_xlabel("Fiber ID")
    axes[1].set_xticks(xticks); axes[1].grid(axis="x", linewidth=0.8)

    axes[2].errorbar(log_qa_frac, frac_out, yerr=err_out,
                     fmt="o", ms=3, lw=0.5, capsize=0, alpha=0.5, color="C2")
    axes[2].plot(x_line, slope * x_line + intercept, color="k", lw=1.5, label="linear fit")
    axes[2].text(0.03, 0.95,
                 f"Pearson r={pearson_r:.2f} (p={pearson_p:.2e})\n"
                 f"Spearman ρ={spearman_r:.2f} (p={spearman_p:.2e})",
                 transform=axes[2].transAxes, va="top", fontsize=9, family="monospace",
                 bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))
    axes[2].set_xlabel("log10(QA failure rate)")
    axes[2].set_ylabel("Outlier fraction")
    axes[2].set_title(f"{name} — outlier fraction vs QA failure rate (per fiber)")
    axes[2].legend()

    fig.suptitle(f"Loa {name} — outlier fraction vs QA failure rate per fiber")
    fig.tight_layout()
    outpath = f"plots/outlier_fraction_vs_qa_per_fiber_{name.lower()}_loa.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

    # ── per-petal 2×5 scatter ─────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 5, figsize=(18, 8), sharex=False, sharey=True)
    for petal, ax in enumerate(axes.flat):
        sl = slice(petal * 500, (petal + 1) * 500)
        x, y, ye = log_qa_frac[sl], frac_out[sl], err_out[sl]
        valid = np.isfinite(x) & np.isfinite(y)
        ax.errorbar(x, y, yerr=ye, fmt="o", ms=3, lw=0.5, capsize=0, alpha=0.5)
        if valid.sum() > 2:
            x_v, y_v  = x[valid], y[valid]
            pr, _     = stats.pearsonr(x_v, y_v)
            sr, _     = stats.spearmanr(x_v, y_v)
            s, b, *_  = stats.linregress(x_v, y_v)
            xl        = np.linspace(x_v.min(), x_v.max(), 100)
            ax.plot(xl, s * xl + b, color="k", lw=1.2)
            ax.text(0.05, 0.95, f"r={pr:.2f}\nρ={sr:.2f}",
                    transform=ax.transAxes, va="top", fontsize=8, family="monospace",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))
        ax.set_title(f"Petal {petal}")
        ax.set_xlabel("log10(QA fail rate)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Outlier fraction")
    fig.suptitle(f"Loa {name} — outlier fraction vs QA failure rate per petal")
    fig.tight_layout()
    outpath = f"plots/qa_correlation_per_petal_{name.lower()}_loa.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")
