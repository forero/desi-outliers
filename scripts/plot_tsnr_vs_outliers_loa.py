import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv"

print("Reading zcatalog (dark only)...")
data = fitsio.read(ZCAT, ext="ZCATALOG", columns=["TARGETID", "TILEID", "TSNR2_LRG", "PROGRAM"])
mask = np.array([p.strip() == "dark" for p in data["PROGRAM"]])
data = data[mask]
print(f"  {len(data):,} dark targets")

df = pd.DataFrame({
    "TARGETID":  data["TARGETID"].byteswap().newbyteorder(),
    "TILEID":    data["TILEID"].byteswap().newbyteorder(),
    "TSNR2_LRG": data["TSNR2_LRG"].byteswap().newbyteorder(),
})

print("Reading outliers...")
outliers = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(outliers["TARGETID"], outliers["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]
print(f"  {df['is_outlier'].sum():,} outliers matched in dark program")

tsnr_all      = df["TSNR2_LRG"].values
tsnr_outliers = df.loc[df["is_outlier"], "TSNR2_LRG"].values

# --- plot 1: normalized histogram ---
fig, ax = plt.subplots(figsize=(8, 5))
bins = np.linspace(np.percentile(tsnr_all, 1), np.percentile(tsnr_all, 99), 60)
ax.hist(tsnr_all,      bins=bins, density=True, alpha=0.6, label="all dark")
ax.hist(tsnr_outliers, bins=bins, density=True, alpha=0.6, label="outliers")
ax.set_xlabel("TSNR2_LRG")
ax.set_ylabel("Probability density")
ax.set_title("Loa dark — TSNR2_LRG distribution")
ax.legend()
fig.tight_layout()
fig.savefig("plots/tsnr_lrg_histogram_loa.png", dpi=150)
plt.close(fig)
print("Saved plots/tsnr_lrg_histogram_loa.png")

# --- plot 2: outlier fraction vs TSNR bin ---
bins = np.linspace(np.percentile(tsnr_all, 1), np.percentile(tsnr_all, 99), 30)
bin_centers = 0.5 * (bins[:-1] + bins[1:])

total, _   = np.histogram(tsnr_all,      bins=bins)
n_out, _   = np.histogram(tsnr_outliers, bins=bins)
fraction   = np.where(total > 0, n_out / total, np.nan)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(bin_centers, fraction, marker="o", ms=4)
ax.set_xlabel("TSNR2_LRG")
ax.set_ylabel("Outlier fraction")
ax.set_title("Loa dark — outlier fraction vs TSNR2_LRG")
fig.tight_layout()
fig.savefig("plots/tsnr_lrg_outlier_fraction_loa.png", dpi=150)
plt.close(fig)
print("Saved plots/tsnr_lrg_outlier_fraction_loa.png")
