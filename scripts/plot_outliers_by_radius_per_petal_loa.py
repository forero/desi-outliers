import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv"
PROGRAMS = ["dark", "bright", "backup"]

print("Reading zcatalog...")
data = fitsio.read(ZCAT, ext="ZCATALOG",
                   columns=["TARGETID", "TILEID", "PROGRAM", "PETAL_LOC",
                             "MEAN_FIBER_X", "MEAN_FIBER_Y"])
df = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().newbyteorder(),
    "TILEID":   data["TILEID"].byteswap().newbyteorder(),
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
    "PETAL":    data["PETAL_LOC"].byteswap().newbyteorder(),
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

bins = np.linspace(0, df["RADIUS"].quantile(0.999), 30)
bin_centers = 0.5 * (bins[:-1] + bins[1:])

for program in PROGRAMS:
    sub = df[df["PROGRAM"] == program]
    fig, axes = plt.subplots(2, 5, figsize=(18, 7), sharex=True, sharey=True)

    for petal, ax in enumerate(axes.flat):
        sp = sub[sub["PETAL"] == petal]
        n_total, _ = np.histogram(sp["RADIUS"], bins=bins)
        n_out,   _ = np.histogram(sp.loc[sp["is_outlier"], "RADIUS"], bins=bins)
        fraction   = np.where(n_total > 0, n_out / n_total, np.nan)
        ax.scatter(bin_centers, fraction, s=10)
        ax.set_title(f"Petal {petal}")
        ax.grid(axis="y", linewidth=0.5)

    for ax in axes[1]:
        ax.set_xlabel("Focal plane radius (mm)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Outlier fraction")

    fig.suptitle(f"Loa {program} — outlier fraction vs radius per petal")
    fig.tight_layout()

    outpath = f"plots/outliers_by_radius_per_petal_{program}_loa.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
