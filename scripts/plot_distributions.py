"""
Outlier distribution plots for Loa and Matterhorn.
Produces per-production and comparison plots for:
  - outliers by program
  - outliers per tile (histogram)
  - outliers per petal (bar chart)
  - outliers by fiber (scatter)
"""
import pandas as pd
import matplotlib.pyplot as plt

PRODUCTIONS = {
    "Matterhorn": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv",
        "tiles":    "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv",
    },
    "Loa": {
        "outliers": "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv",
        "tiles":    "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv",
    },
}
PROGRAMS = ["dark", "bright", "backup"]
PETALS   = range(10)


def load(paths):
    out   = pd.read_csv(paths["outliers"], usecols=["TILEID", "FIBER"])
    tiles = pd.read_csv(paths["tiles"],    usecols=["TILEID", "PROGRAM"])
    df    = out.merge(tiles, on="TILEID", how="left")
    df["PETAL"] = df["FIBER"] // 500
    return df


# ── load ──────────────────────────────────────────────────────────────────────
data = {}
for name, paths in PRODUCTIONS.items():
    print(f"Loading {name}...")
    data[name] = load(paths)

# ── by_program ────────────────────────────────────────────────────────────────
prog_counts = {}
for name, df in data.items():
    counts = df["PROGRAM"].value_counts().sort_index()
    prog_counts[name] = counts

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(counts.index, counts.values)
    ax.set_title(f"{name} — outliers by program")
    ax.set_xlabel("Program")
    ax.set_ylabel("Number of outliers")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    outpath = f"plots/outliers_by_program_{name.lower()}.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

programs_all = sorted(set().union(*[c.index for c in prog_counts.values()]))
x = range(len(programs_all)); width = 0.35
fig, ax = plt.subplots(figsize=(7, 5))
for i, (name, counts) in enumerate(prog_counts.items()):
    vals   = [counts.get(p, 0) for p in programs_all]
    offset = (i - 0.5) * width
    ax.bar([xi + offset for xi in x], vals, width, label=name)
ax.set_xticks(list(x)); ax.set_xticklabels(programs_all, rotation=45)
ax.set_xlabel("Program"); ax.set_ylabel("Number of outliers")
ax.set_title("Outliers by program — both productions"); ax.legend()
fig.tight_layout()
outpath = "plots/outliers_by_program_comparison.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

# ── per_tile ──────────────────────────────────────────────────────────────────
tile_counts = {}
for name, df in data.items():
    for program in PROGRAMS:
        tile_counts[(name, program)] = (
            df[df["PROGRAM"] == program].groupby("TILEID").size()
        )

for name in PRODUCTIONS:
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=False)
    for ax, program in zip(axes, PROGRAMS):
        counts = tile_counts[(name, program)]
        ax.hist(counts, bins=50,
                label=f"median={counts.median():.0f}, std={counts.std():.0f}")
        ax.set_title(program); ax.set_xlabel("Outliers per tile")
        ax.set_ylabel("Number of tiles"); ax.legend()
    fig.suptitle(f"{name} — outliers per tile"); fig.tight_layout()
    outpath = f"plots/outliers_per_tile_{name.lower()}.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=False)
for ax, program in zip(axes, PROGRAMS):
    for name in PRODUCTIONS:
        counts = tile_counts[(name, program)]
        ax.hist(counts, bins=50, alpha=0.6, density=True,
                label=f"{name} (median={counts.median():.0f})")
    ax.set_title(program); ax.set_xlabel("Outliers per tile")
    ax.set_ylabel("Probability density"); ax.legend()
fig.suptitle("Outliers per tile — both productions"); fig.tight_layout()
outpath = "plots/outliers_per_tile_comparison.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

# ── per_petal ─────────────────────────────────────────────────────────────────
petal_counts = {}
for name, df in data.items():
    for program in PROGRAMS:
        petal_counts[(name, program)] = (
            df[df["PROGRAM"] == program]
            .groupby("PETAL").size()
            .reindex(PETALS, fill_value=0)
        )

for name in PRODUCTIONS:
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    for ax, program in zip(axes, PROGRAMS):
        counts = petal_counts[(name, program)]
        ax.bar(counts.index, counts.values,
               label=f"median={counts.median():.0f}, std={counts.std():.0f}")
        ax.set_title(program); ax.set_ylabel("Number of outliers")
        ax.set_xticks(list(PETALS)); ax.legend()
    axes[-1].set_xlabel("Petal ID")
    fig.suptitle(f"{name} — outliers per petal"); fig.tight_layout()
    outpath = f"plots/outliers_per_petal_{name.lower()}.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

width = 0.35
fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
for ax, program in zip(axes, PROGRAMS):
    for i, name in enumerate(PRODUCTIONS):
        counts = petal_counts[(name, program)]
        norm   = counts / counts.sum()
        offset = (i - 0.5) * width
        ax.bar([p + offset for p in PETALS], norm.values, width, alpha=0.7,
               label=f"{name} (median={counts.median():.0f})")
    ax.set_title(program); ax.set_ylabel("Fraction of outliers")
    ax.set_xticks(list(PETALS)); ax.legend()
axes[-1].set_xlabel("Petal ID")
fig.suptitle("Outliers per petal — both productions"); fig.tight_layout()
outpath = "plots/outliers_per_petal_comparison.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

# ── by_fiber ──────────────────────────────────────────────────────────────────
for name, df in data.items():
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    for ax, program in zip(axes, PROGRAMS):
        counts = df[df["PROGRAM"] == program].groupby("FIBER").size()
        ax.scatter(counts.index, counts.values, s=2, alpha=0.6)
        ax.set_ylabel("Number of outliers"); ax.set_title(program)
        ax.set_xticks(range(0, 5001, 500)); ax.grid(axis="x", linewidth=0.8)
    axes[-1].set_xlabel("Fiber ID")
    fig.suptitle(f"{name} — outliers per fiber ID"); fig.tight_layout()
    outpath = f"plots/outliers_by_fiber_{name.lower()}.png"
    fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")
