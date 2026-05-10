"""
Outlier fraction vs focal plane radius for Loa.
Produces:
  - outliers_by_radius_loa.png          (3 programs, overall)
  - outliers_by_radius_per_petal_*_loa.png  (per-petal, per program)
"""
import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
PROGRAMS = ["dark", "bright", "backup"]

print("Reading zcatalog...")
raw = fitsio.read(ZCAT, ext="ZCATALOG",
                  columns=["TARGETID", "TILEID", "PROGRAM", "PETAL_LOC",
                           "MEAN_FIBER_X", "MEAN_FIBER_Y"])
df = pd.DataFrame({
    "TARGETID": raw["TARGETID"].byteswap().view(raw["TARGETID"].dtype.newbyteorder()),
    "TILEID":   raw["TILEID"].byteswap().view(raw["TILEID"].dtype.newbyteorder()),
    "PROGRAM":  [p.strip() for p in raw["PROGRAM"]],
    "PETAL":    raw["PETAL_LOC"].byteswap().view(raw["PETAL_LOC"].dtype.newbyteorder()),
    "X":        raw["MEAN_FIBER_X"].byteswap().view(raw["MEAN_FIBER_X"].dtype.newbyteorder()),
    "Y":        raw["MEAN_FIBER_Y"].byteswap().view(raw["MEAN_FIBER_Y"].dtype.newbyteorder()),
})
df["RADIUS"] = np.sqrt(df["X"]**2 + df["Y"]**2)
print(f"  {len(df):,} targets")

print("Reading outliers...")
out = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(out["TARGETID"], out["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]

# ── overall by radius ─────────────────────────────────────────────────────────
bins40       = np.linspace(0, df["RADIUS"].quantile(0.999), 40)
bin_centers40 = 0.5 * (bins40[:-1] + bins40[1:])

fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
for ax, program in zip(axes, PROGRAMS):
    sub      = df[df["PROGRAM"] == program]
    n_total, _ = np.histogram(sub["RADIUS"], bins=bins40)
    n_out,   _ = np.histogram(sub.loc[sub["is_outlier"], "RADIUS"], bins=bins40)
    fraction   = np.where(n_total > 0, n_out / n_total, np.nan)
    ax.scatter(bin_centers40, fraction, s=15)
    ax.set_title(program); ax.set_ylabel("Outlier fraction")
    ax.grid(axis="y", linewidth=0.5)
axes[-1].set_xlabel("Focal plane radius (mm)")
fig.suptitle("Loa — outlier fraction vs focal plane radius")
fig.tight_layout()
outpath = "plots/outliers_by_radius_loa.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

# ── per-petal by radius ───────────────────────────────────────────────────────
bins30        = np.linspace(0, df["RADIUS"].quantile(0.999), 30)
bin_centers30 = 0.5 * (bins30[:-1] + bins30[1:])

for program in PROGRAMS:
    sub = df[df["PROGRAM"] == program]
    fig, axes = plt.subplots(2, 5, figsize=(18, 7), sharex=True, sharey=True)
    for petal, ax in enumerate(axes.flat):
        sp       = sub[sub["PETAL"] == petal]
        n_total, _ = np.histogram(sp["RADIUS"], bins=bins30)
        n_out,   _ = np.histogram(sp.loc[sp["is_outlier"], "RADIUS"], bins=bins30)
        fraction   = np.where(n_total > 0, n_out / n_total, np.nan)
        err        = np.where(n_total > 0, np.sqrt(n_out) / n_total, np.nan)
        ax.errorbar(bin_centers30, fraction, yerr=err, fmt="o", ms=4, capsize=2, lw=0.8)
        ax.set_title(f"Petal {petal}"); ax.grid(axis="y", linewidth=0.5)
    for ax in axes[1]:
        ax.set_xlabel("Focal plane radius (mm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Outlier fraction")
    fig.suptitle(f"Loa {program} — outlier fraction vs radius per petal")
    fig.tight_layout()
    outpath = f"plots/outliers_by_radius_per_petal_{program}_loa.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")
