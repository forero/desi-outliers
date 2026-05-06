import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv"
PROGRAMS = ["dark", "bright", "backup"]

print("Reading zcatalog...")
data = fitsio.read(ZCAT, ext="ZCATALOG",
                   columns=["TARGETID", "TILEID", "PROGRAM", "MEAN_FIBER_X", "MEAN_FIBER_Y"])
df = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().newbyteorder(),
    "TILEID":   data["TILEID"].byteswap().newbyteorder(),
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
    "X":        data["MEAN_FIBER_X"].byteswap().newbyteorder(),
    "Y":        data["MEAN_FIBER_Y"].byteswap().newbyteorder(),
})
df["RADIUS"] = np.sqrt(df["X"]**2 + df["Y"]**2)
print(f"  {len(df):,} total targets")

print("Reading outliers...")
outliers = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(outliers["TARGETID"], outliers["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]

bins = np.linspace(0, df["RADIUS"].quantile(0.999), 40)
bin_centers = 0.5 * (bins[:-1] + bins[1:])

fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

for ax, program in zip(axes, PROGRAMS):
    sub = df[df["PROGRAM"] == program]
    n_total,  _ = np.histogram(sub["RADIUS"], bins=bins)
    n_out,    _ = np.histogram(sub.loc[sub["is_outlier"], "RADIUS"], bins=bins)
    fraction    = np.where(n_total > 0, n_out / n_total, np.nan)

    ax.scatter(bin_centers, fraction, s=15)
    ax.set_title(program)
    ax.set_ylabel("Outlier fraction")
    ax.grid(axis="y", linewidth=0.5)

axes[-1].set_xlabel("Focal plane radius (mm)")
fig.suptitle("Loa — outlier fraction vs focal plane radius")
fig.tight_layout()

outpath = "plots/outliers_by_radius_loa.png"
fig.savefig(outpath, dpi=150)
print(f"Saved {outpath}")
