import pandas as pd
import numpy as np
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
out["PETAL"] = out["FIBER"] // 500

fig, axes = plt.subplots(3, 1, figsize=(14, 12))

for ax, program in zip(axes, PROGRAMS):
    sub = out[out["PROGRAM"] == program]
    pivot = (
        sub.groupby(["MONTH", "PETAL"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=range(10), fill_value=0)
    )
    months = [str(m) for m in pivot.index]
    im = ax.imshow(pivot.values.T, aspect="auto", origin="lower",
                   cmap="YlOrRd", interpolation="nearest")
    ax.set_yticks(range(10))
    ax.set_yticklabels([f"Petal {p}" for p in range(10)])
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=90, fontsize=7)
    ax.set_title(program)
    fig.colorbar(im, ax=ax, label="N outliers")

fig.suptitle("Matterhorn — outliers heatmap: month × petal")
fig.tight_layout()

outpath = "plots/outliers_heatmap_month_petal_matterhorn.png"
fig.savefig(outpath, dpi=150)
print(f"Saved {outpath}")
