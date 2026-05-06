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

# per-tile outlier counts keyed by (production, program)
all_counts = {}

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])
    merged = outliers.merge(tiles, on="TILEID", how="left")

    for program in PROGRAMS:
        counts = (
            merged[merged["PROGRAM"] == program]
            .groupby("TILEID")
            .size()
        )
        all_counts[(name, program)] = counts

# individual plots
for name in PRODUCTIONS:
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=False)

    for ax, program in zip(axes, PROGRAMS):
        counts = all_counts[(name, program)]
        median = counts.median()
        std = counts.std()
        label = f"median={median:.0f}, std={std:.0f}"
        ax.hist(counts, bins=50, label=label)
        ax.set_title(program)
        ax.set_xlabel("Outliers per tile")
        ax.set_ylabel("Number of tiles")
        ax.legend()

    fig.suptitle(f"{name} — outliers per tile")
    fig.tight_layout()

    outpath = f"plots/outliers_per_tile_{name.lower()}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")

# comparison plot
fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=False)

for ax, program in zip(axes, PROGRAMS):
    for name in PRODUCTIONS:
        counts = all_counts[(name, program)]
        ax.hist(counts, bins=50, alpha=0.6, label=name)
    ax.set_title(program)
    ax.set_xlabel("Outliers per tile")
    ax.set_ylabel("Number of tiles")
    ax.legend()

fig.suptitle("Outliers per tile — both productions")
fig.tight_layout()

outpath = "plots/outliers_per_tile_comparison.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")
