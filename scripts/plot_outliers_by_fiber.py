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

PROGRAMS = ["bright", "dark", "backup"]

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID", "FIBER"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])
    merged = outliers.merge(tiles, on="TILEID", how="left")

    fig, ax = plt.subplots(figsize=(10, 5))

    for program in PROGRAMS:
        subset = merged[merged["PROGRAM"] == program]
        counts = subset.groupby("FIBER").size()
        ax.plot(counts.index, counts.values, label=program, alpha=0.8)

    ax.set_xlabel("Fiber ID")
    ax.set_ylabel("Number of outliers")
    ax.set_title(f"{name} — outliers per fiber ID")
    ax.legend()
    fig.tight_layout()

    outpath = f"plots/outliers_by_fiber_{name.lower()}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
