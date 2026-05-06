import pandas as pd
import matplotlib.pyplot as plt

PRODUCTIONS = {
    "Matterhorn": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/daily/tiles-daily.csv",
    },
    "Loa": {
        "outliers": "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv",
    },
}

fig, axes = plt.subplots(1, 2, figsize=(10, 5))

for ax, (name, paths) in zip(axes, PRODUCTIONS.items()):
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])

    counts = (
        outliers.merge(tiles, on="TILEID", how="left")
        ["PROGRAM"]
        .value_counts()
        .sort_index()
    )

    ax.bar(counts.index, counts.values)
    ax.set_title(name)
    ax.set_xlabel("Program")
    ax.set_ylabel("Number of outliers")
    ax.tick_params(axis="x", rotation=45)

fig.suptitle("DESI outliers by program")
fig.tight_layout()
fig.savefig("plots/outliers_by_program.png", dpi=150)
print("Saved plots/outliers_by_program.png")
