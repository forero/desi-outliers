"""
Run HDBSCAN on a single UMAP embedding batch, find cluster centres,
and produce a diagnostic scatter plot.

Usage: python scripts/dbscan_umap_batch.py [npz_path] [min_cluster_size] [min_samples]
Defaults: min_cluster_size=200  min_samples=50
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import HDBSCAN

NPZ_FILE         = sys.argv[1] if len(sys.argv) > 1 else (
    "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/"
    "outlier_umap_batches_test/outlier_umap_batch_0001.npz"
)
MIN_CLUSTER_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 200
MIN_SAMPLES      = int(sys.argv[3]) if len(sys.argv) > 3 else 50

print(f"Loading {NPZ_FILE}")
f   = np.load(NPZ_FILE)
emb = f["embedding"]          # (N, 2)
print(f"  {len(emb):,} points")

# ── HDBSCAN ───────────────────────────────────────────────────────────────────
print(f"Running HDBSCAN (min_cluster_size={MIN_CLUSTER_SIZE}, min_samples={MIN_SAMPLES})...")
db     = HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, min_samples=MIN_SAMPLES, n_jobs=-1).fit(emb)
labels = db.labels_

n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise    = (labels == -1).sum()
print(f"  Clusters found : {n_clusters}")
print(f"  Noise points   : {n_noise:,}  ({100*n_noise/len(labels):.1f}%)")

# ── cluster centres and closest point ────────────────────────────────────────
print("\nCluster  Size    Centre (x, y)          Closest TARGETID")
print("-" * 65)
cluster_info = []
for cid in sorted(set(labels)):
    if cid == -1:
        continue
    mask   = labels == cid
    pts    = emb[mask]
    centre = pts.mean(axis=0)
    dists  = np.linalg.norm(pts - centre, axis=1)
    idx_local  = np.argmin(dists)
    idx_global = np.where(mask)[0][idx_local]
    targetid   = int(f["targetids"][idx_global])
    tileid     = int(f["tileids"][idx_global])
    fiber      = int(f["fibers"][idx_global])
    cluster_info.append({
        "cluster":   cid,
        "size":      mask.sum(),
        "cx":        centre[0],
        "cy":        centre[1],
        "targetid":  targetid,
        "tileid":    tileid,
        "fiber":     fiber,
        "idx":       idx_global,
    })
    print(f"  {cid:4d}   {mask.sum():6,}   ({centre[0]:7.2f}, {centre[1]:7.2f})   {targetid}")

# ── diagnostic plot ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))

# noise in grey
noise_mask = labels == -1
ax.scatter(emb[noise_mask, 0], emb[noise_mask, 1],
           s=0.3, c="lightgrey", alpha=0.3, rasterized=True, label=f"Noise ({n_noise:,})")

# clusters coloured by label
cmap = plt.cm.tab20
for info in cluster_info:
    mask  = labels == info["cluster"]
    color = cmap(info["cluster"] % 20)
    ax.scatter(emb[mask, 0], emb[mask, 1],
               s=0.5, color=color, alpha=0.5, rasterized=True)
    # mark centre
    ax.scatter(info["cx"], info["cy"], marker="*", s=120,
               color=color, edgecolors="k", linewidths=0.5, zorder=5)
    # label cluster id
    ax.text(info["cx"], info["cy"] + 0.3, str(info["cluster"]),
            fontsize=7, ha="center", va="bottom", color="k",
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.6, linewidth=0))

ax.set_xlabel("UMAP 1")
ax.set_ylabel("UMAP 2")
ax.set_title(f"HDBSCAN clustering — {n_clusters} clusters  |  min_cluster_size={MIN_CLUSTER_SIZE}  min_samples={MIN_SAMPLES}\n"
             f"{len(emb):,} points, {n_noise:,} noise ({100*n_noise/len(labels):.1f}%)")
ax.legend(markerscale=6, loc="upper right", fontsize=8)

outpath = "plots/dbscan_umap_batch.png"
fig.savefig(outpath, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved {outpath}")

# ── write cluster representatives to CSV ─────────────────────────────────────
import pandas as pd, pathlib
reps = pd.DataFrame([
    {"cluster": d["cluster"], "size": d["size"],
     "cx": d["cx"], "cy": d["cy"],
     "targetid": d["targetid"], "tileid": d["tileid"], "fiber": d["fiber"]}
    for d in cluster_info
])
pathlib.Path("data").mkdir(exist_ok=True)
csv_path = "data/cluster_representatives.csv"
reps.to_csv(csv_path, index=False)
print(f"Saved {csv_path}  ({len(reps)} clusters)")

labels_path = "data/cluster_labels.npy"
np.save(labels_path, labels)
print(f"Saved {labels_path}")
