import sys
import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"

PROGRAM_TSNR = {
    "dark":   "TSNR2_LRG",
    "bright": "TSNR2_BGS",
    "backup": "TSNR2_BGS",
}

program = sys.argv[1] if len(sys.argv) > 1 else "dark"
tsnr_col = PROGRAM_TSNR[program]

print(f"Reading zcatalog ({program} only, {tsnr_col})...")
data = fitsio.read(ZCAT, ext="ZCATALOG", columns=["TARGETID", "TILEID", tsnr_col, "PROGRAM"])
mask = np.array([p.strip() == program for p in data["PROGRAM"]])
data = data[mask]
print(f"  {len(data):,} {program} targets")

df = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().view(data["TARGETID"].dtype.newbyteorder()),
    "TILEID":   data["TILEID"].byteswap().view(data["TILEID"].dtype.newbyteorder()),
    "TSNR":     data[tsnr_col].byteswap().view(data[tsnr_col].dtype.newbyteorder()),
})

print("Reading outliers...")
outliers = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(outliers["TARGETID"], outliers["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]
print(f"  {df['is_outlier'].sum():,} outliers matched in {program} program")

tsnr_all      = df["TSNR"].values
tsnr_outliers = df.loc[df["is_outlier"], "TSNR"].values

# --- plot 1: normalized histogram ---
bins = np.linspace(np.percentile(tsnr_all, 1), np.percentile(tsnr_all, 99), 60)
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(tsnr_all,      bins=bins, density=True, alpha=0.6, label=f"all {program}")
ax.hist(tsnr_outliers, bins=bins, density=True, alpha=0.6, label="outliers")
ax.set_xlabel(tsnr_col)
ax.set_ylabel("Probability density")
ax.set_title(f"Loa {program} — {tsnr_col} distribution")
ax.legend()
fig.tight_layout()
outpath = f"plots/tsnr_{program}_histogram_loa.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")

# --- plot 2: outlier fraction vs TSNR bin ---
bins = np.linspace(np.percentile(tsnr_all, 1), np.percentile(tsnr_all, 99), 30)
bin_centers = 0.5 * (bins[:-1] + bins[1:])
total, _ = np.histogram(tsnr_all,      bins=bins)
n_out, _ = np.histogram(tsnr_outliers, bins=bins)
fraction = np.where(total > 0, n_out / total, np.nan)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(bin_centers, fraction, marker="o", ms=4)
ax.set_xlabel(tsnr_col)
ax.set_ylabel("Outlier fraction")
ax.set_title(f"Loa {program} — outlier fraction vs {tsnr_col}")
fig.tight_layout()
outpath = f"plots/tsnr_{program}_outlier_fraction_loa.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")
