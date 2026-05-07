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
PETALS = range(10)

all_counts = {}

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID", "FIBER"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])
    merged = outliers.merge(tiles, on="TILEID", how="left")
    merged["PETAL"] = merged["FIBER"] // 500

    for program in PROGRAMS:
        counts = (
            merged[merged["PROGRAM"] == program]
            .groupby("PETAL")
            .size()
            .reindex(PETALS, fill_value=0)
        )
        all_counts[(name, program)] = counts

# individual plots
for name in PRODUCTIONS:
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

    for ax, program in zip(axes, PROGRAMS):
        counts = all_counts[(name, program)]
        median = counts.median()
        std = counts.std()
        label = f"median={median:.0f}, std={std:.0f}"
        ax.bar(counts.index, counts.values, label=label)
        ax.set_title(program)
        ax.set_ylabel("Number of outliers")
        ax.set_xticks(list(PETALS))
        ax.legend()

    axes[-1].set_xlabel("Petal ID")
    fig.suptitle(f"{name} — outliers per petal")
    fig.tight_layout()

    outpath = f"plots/outliers_per_petal_{name.lower()}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved {outpath}")

# comparison plot
width = 0.35
fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

for ax, program in zip(axes, PROGRAMS):
    for i, name in enumerate(PRODUCTIONS):
        counts = all_counts[(name, program)]
        norm = counts / counts.sum()
        median = counts.median()
        label = f"{name} (median={median:.0f})"
        offset = (i - 0.5) * width
        ax.bar([p + offset for p in PETALS], norm.values, width, alpha=0.7, label=label)
    ax.set_title(program)
    ax.set_ylabel("Fraction of outliers")
    ax.set_xticks(list(PETALS))
    ax.legend()

axes[-1].set_xlabel("Petal ID")
fig.suptitle("Outliers per petal — both productions")
fig.tight_layout()

outpath = "plots/outliers_per_petal_comparison.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")
