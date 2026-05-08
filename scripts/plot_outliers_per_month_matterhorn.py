import pandas as pd
import matplotlib.pyplot as plt

OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
TILES    = "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv"
PROGRAMS = ["dark", "bright", "backup"]

print("Reading outliers...")
out = pd.read_csv(OUTLIERS, usecols=["TILEID", "FIBER", "NIGHT"])
tiles = pd.read_csv(TILES, usecols=["TILEID", "PROGRAM"])
out = out.merge(tiles, on="TILEID", how="left")

out["NIGHT"] = out["NIGHT"].astype(str)
out["MONTH"] = pd.to_datetime(out["NIGHT"], format="%Y%m%d").dt.to_period("M")

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

for ax, program in zip(axes, PROGRAMS):
    sub = out[out["PROGRAM"] == program]
    counts = sub.groupby("MONTH").size()
    ax.bar(counts.index.astype(str), counts.values)
    ax.set_title(program)
    ax.set_ylabel("Number of outliers")
    ax.tick_params(axis="x", rotation=45)

axes[-1].set_xlabel("Month")
fig.suptitle("Matterhorn — outliers per month by program")
fig.tight_layout()

outpath = "plots/outliers_per_month_matterhorn.png"
fig.savefig(outpath, dpi=150)
print(f"Saved {outpath}")
