import pandas as pd
import matplotlib.pyplot as plt

PRODUCTIONS = {
    "Matterhorn": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv",
    },
    "Loa": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv",
        "tiles": "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv",
    },
}

all_counts = {}

for name, paths in PRODUCTIONS.items():
    outliers = pd.read_csv(paths["outliers"], usecols=["TILEID"])
    tiles = pd.read_csv(paths["tiles"], usecols=["TILEID", "PROGRAM"])

    counts = (
        outliers.merge(tiles, on="TILEID", how="left")
        ["PROGRAM"]
        .value_counts()
        .sort_index()
    )
    all_counts[name] = counts

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

# comparison plot
programs = sorted(set().union(*[c.index for c in all_counts.values()]))
x = range(len(programs))
width = 0.35

fig, ax = plt.subplots(figsize=(7, 5))
for i, (name, counts) in enumerate(all_counts.items()):
    vals = [counts.get(p, 0) for p in programs]
    offset = (i - 0.5) * width
    ax.bar([xi + offset for xi in x], vals, width, label=name)

ax.set_yscale("linear")
ax.set_xticks(list(x))
ax.set_xticklabels(programs, rotation=45)
ax.set_xlabel("Program")
ax.set_ylabel("Number of outliers")
ax.set_title("Outliers by program — both productions")
ax.legend()
fig.tight_layout()

outpath = "plots/outliers_by_program_comparison.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")
