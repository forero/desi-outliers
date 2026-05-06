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

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])

    counts = (
        outliers.merge(tiles, on="TILEID", how="left")
        ["PROGRAM"]
        .value_counts()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(counts.index, counts.values)
    ax.set_title(f"{name} — outliers by program")
    ax.set_xlabel("Program")
    ax.set_ylabel("Number of outliers")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    outpath = f"plots/outliers_by_program_{name.lower()}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")
