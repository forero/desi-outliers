import pandas as pd
import matplotlib.pyplot as plt

PRODUCTIONS = {
    "Matterhorn": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv",
    },
    "Loa": {
        "outliers": "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv",
    },
}

PROGRAMS = ["dark", "bright", "backup"]

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID", "FIBER"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])
    merged = outliers.merge(tiles, on="TILEID", how="left")

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    for ax, program in zip(axes, PROGRAMS):
        subset = merged[merged["PROGRAM"] == program]
        counts = subset.groupby("FIBER").size()
        ax.scatter(counts.index, counts.values, s=2, alpha=0.6)
        ax.set_ylabel("Number of outliers")
        ax.set_title(program)
        ax.set_xticks(range(0, 5001, 500))
        ax.grid(axis="x", linewidth=0.8)

    axes[-1].set_xlabel("Fiber ID")
    fig.suptitle(f"{name} — outliers per fiber ID")
    fig.tight_layout()

    outpath = f"plots/outliers_by_fiber_{name.lower()}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
