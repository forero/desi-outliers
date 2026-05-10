"""
Matterhorn outlier time-series plots.
Produces:
  - outliers_per_month_matterhorn.png         (bar chart per month)
  - outliers_heatmap_month_petal_matterhorn.png  (outlier fraction heatmap)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
TILES    = "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv"
PROGRAMS = ["dark", "bright", "backup"]

print("Reading data...")
out   = pd.read_csv(OUTLIERS, usecols=["TILEID", "FIBER", "NIGHT"])
tiles = pd.read_csv(TILES,    usecols=["TILEID", "PROGRAM", "LASTNIGHT"])
out   = out.merge(tiles[["TILEID", "PROGRAM"]], on="TILEID", how="left")

out["NIGHT"] = out["NIGHT"].astype(str)
out["MONTH"] = pd.to_datetime(out["NIGHT"], format="%Y%m%d").dt.to_period("M")
out["PETAL"] = out["FIBER"] // 500

tiles["MONTH"] = pd.to_datetime(
    tiles["LASTNIGHT"].astype(str), format="%Y%m%d"
).dt.to_period("M")
n_tiles = tiles.groupby(["MONTH", "PROGRAM"]).size().reset_index(name="N_TILES")

# ── per-month bar chart ───────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
for ax, program in zip(axes, PROGRAMS):
    counts = out[out["PROGRAM"] == program].groupby("MONTH").size()
    ax.bar(counts.index.astype(str), counts.values)
    ax.set_title(program); ax.set_ylabel("Number of outliers")
    ax.tick_params(axis="x", rotation=45)
axes[-1].set_xlabel("Month")
fig.suptitle("Matterhorn — outliers per month by program")
fig.tight_layout()
outpath = "plots/outliers_per_month_matterhorn.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")

# ── outlier fraction heatmap (month × petal) ──────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
for ax, program in zip(axes, PROGRAMS):
    sub   = out[out["PROGRAM"] == program]
    n_out = (
        sub.groupby(["MONTH", "PETAL"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=range(10), fill_value=0)
    )
    ntiles = (
        n_tiles[n_tiles["PROGRAM"] == program]
        .set_index("MONTH")["N_TILES"]
        .reindex(n_out.index, fill_value=0)
    )
    denom    = np.outer(ntiles.values, np.full(10, 500))
    fraction = np.where(denom > 0, n_out.values / denom, np.nan)

    months = [str(m) for m in n_out.index]
    im = ax.imshow(fraction.T, aspect="auto", origin="lower",
                   cmap="YlOrRd", interpolation="nearest")
    ax.set_yticks(range(10)); ax.set_yticklabels([f"Petal {p}" for p in range(10)])
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=90, fontsize=7)
    ax.set_title(program)
    fig.colorbar(im, ax=ax, label="Outlier fraction")

fig.suptitle("Matterhorn — outlier fraction heatmap: month × petal")
fig.tight_layout()
outpath = "plots/outliers_heatmap_month_petal_matterhorn.png"
fig.savefig(outpath, dpi=150); plt.close(fig); print(f"Saved {outpath}")
