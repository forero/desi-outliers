"""
Run HDBSCAN on all Loa UMAP batches and generate per-batch HTML reports.

For each batch produces:
  data/cluster_labels_loa_{NNNN}.npy
  data/cluster_representatives_loa_{NNNN}.csv
  html/all_clusters_loa_{NNNN}.html  (copied to CFS)
"""
import numpy as np
import pandas as pd
import pathlib, shutil
from sklearn.cluster import HDBSCAN

BATCH_DIR        = pathlib.Path("/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/outlier_umap_batches")
SPECPROD         = "loa"
BASE_URL         = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra"
MIN_CLUSTER_SIZE = 200
MIN_SAMPLES      = 50
N_SAMPLE         = 10
RNG_SEED         = 42
CFS_DIR          = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")

pathlib.Path("data").mkdir(exist_ok=True)
pathlib.Path("html").mkdir(exist_ok=True)
CFS_DIR.mkdir(parents=True, exist_ok=True)

batch_files = sorted(BATCH_DIR.glob("outlier_umap_batch_????.npz"))

for npz_path in batch_files:
    tag = npz_path.stem.split("_")[-1]          # e.g. "0001"
    print(f"\n{'='*60}")
    print(f"Batch {tag}: {npz_path.name}")
    print(f"{'='*60}")

    f   = np.load(npz_path)
    emb = f["embedding"]
    print(f"  {len(emb):,} points")

    # ── HDBSCAN ───────────────────────────────────────────────────────────────
    print(f"  Running HDBSCAN (min_cluster_size={MIN_CLUSTER_SIZE}, min_samples={MIN_SAMPLES})...")
    db     = HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, min_samples=MIN_SAMPLES, n_jobs=-1).fit(emb)
    labels = db.labels_

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = (labels == -1).sum()
    print(f"  Clusters : {n_clusters}   Noise : {n_noise:,} ({100*n_noise/len(labels):.1f}%)")

    labels_path = f"data/cluster_labels_loa_{tag}.npy"
    np.save(labels_path, labels)

    # ── cluster representatives ────────────────────────────────────────────────
    unique, counts = np.unique(labels[labels >= 0], return_counts=True)
    reps = []
    for cid, size in zip(unique, counts):
        mask   = labels == cid
        pts    = emb[mask]
        centre = pts.mean(axis=0)
        dists  = np.linalg.norm(pts - centre, axis=1)
        ig     = np.where(mask)[0][np.argmin(dists)]
        reps.append({
            "cluster":  cid,
            "size":     size,
            "cx":       centre[0],
            "cy":       centre[1],
            "targetid": int(f["targetids"][ig]),
            "tileid":   int(f["tileids"][ig]),
            "fiber":    int(f["fibers"][ig]),
        })
    csv_path = f"data/cluster_representatives_loa_{tag}.csv"
    pd.DataFrame(reps).to_csv(csv_path, index=False)
    print(f"  Saved {labels_path}  {csv_path}")

    # ── HTML ──────────────────────────────────────────────────────────────────
    order  = np.argsort(-counts)
    unique = unique[order]
    counts = counts[order]

    all_section_targetids = []
    sections_html = ""

    for cid, size in zip(unique, counts):
        indices = np.where(labels == cid)[0]
        centre  = emb[indices].mean(axis=0)
        dists   = np.linalg.norm(emb[indices] - centre, axis=1)
        top10   = indices[np.argsort(dists)[:N_SAMPLE]]

        targetids = [int(f["targetids"][i]) for i in top10]
        tileids   = [int(f["tileids"][i])   for i in top10]
        fibers    = [int(f["fibers"][i])    for i in top10]
        nights    = [int(f["nights"][i])    for i in top10]

        all_section_targetids.extend(str(t) for t in targetids)

        cluster_url = f"{BASE_URL}/" + ",".join(str(t) for t in targetids)

        rows = ""
        for targetid, tileid, fiber, night in zip(targetids, tileids, fibers, nights):
            tile_url = f"{BASE_URL}/tiles/{tileid}/{fiber}"
            rows += f"""
          <tr>
            <td>{targetid}</td>
            <td>{tileid}</td>
            <td>{fiber}</td>
            <td>{night}</td>
            <td><a href="{tile_url}" target="_blank">inspector</a></td>
          </tr>"""

        sections_html += f"""
  <div class="cluster">
    <h2>Cluster {cid} &mdash; {size:,} spectra &nbsp;
      <span class="centre">(centre: {centre[0]:.2f}, {centre[1]:.2f})</span>
      &nbsp;<a href="{cluster_url}" target="_blank">[view {N_SAMPLE} in inspector]</a>
    </h2>
    <table>
      <thead>
        <tr><th>TARGETID</th><th>TILEID</th><th>FIBER</th><th>NIGHT</th><th>Inspector</th></tr>
      </thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>"""

    # noise section
    noise_indices = np.where(labels == -1)[0]
    rng           = np.random.default_rng(RNG_SEED)
    noise_sample  = rng.choice(noise_indices, size=min(N_SAMPLE, len(noise_indices)), replace=False)

    noise_targetids = [int(f["targetids"][i]) for i in noise_sample]
    noise_tileids   = [int(f["tileids"][i])   for i in noise_sample]
    noise_fibers    = [int(f["fibers"][i])    for i in noise_sample]
    noise_nights    = [int(f["nights"][i])    for i in noise_sample]

    noise_cluster_url = f"{BASE_URL}/" + ",".join(str(t) for t in noise_targetids)

    noise_rows = ""
    for targetid, tileid, fiber, night in zip(noise_targetids, noise_tileids, noise_fibers, noise_nights):
        tile_url = f"{BASE_URL}/tiles/{tileid}/{fiber}"
        noise_rows += f"""
          <tr>
            <td>{targetid}</td>
            <td>{tileid}</td>
            <td>{fiber}</td>
            <td>{night}</td>
            <td><a href="{tile_url}" target="_blank">inspector</a></td>
          </tr>"""

    noise_html = f"""
  <div class="cluster noise-section">
    <h2>Noise (unassigned) &mdash; {len(noise_indices):,} spectra &nbsp;
      <span class="centre">(not assigned to any cluster)</span>
      &nbsp;<a href="{noise_cluster_url}" target="_blank">[view {len(noise_sample)} in inspector]</a>
    </h2>
    <table>
      <thead>
        <tr><th>TARGETID</th><th>TILEID</th><th>FIBER</th><th>NIGHT</th><th>Inspector</th></tr>
      </thead>
      <tbody>{noise_rows}
      </tbody>
    </table>
  </div>"""

    all_url = f"{BASE_URL}/" + ",".join(all_section_targetids)
    n_total = len(all_section_targetids)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HDBSCAN clusters — Loa batch {tag}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1100px; }}
    h1   {{ font-size: 1.4em; }}
    h2   {{ font-size: 1.1em; margin-top: 2em; border-bottom: 1px solid #ccc;
            padding-bottom: 4px; }}
    .centre {{ color: #666; font-weight: normal; font-size: 0.9em; }}
    .all-link {{ margin-bottom: 1em; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 0.5em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 8px; text-align: left; font-size: 0.9em; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; }}
    .cluster {{ margin-bottom: 1.5em; }}
    .noise-section {{ border-top: 2px solid #999; padding-top: 0.5em; }}
  </style>
</head>
<body>
  <h1>HDBSCAN clusters — Loa batch {tag} ({n_clusters} clusters, {len(emb):,} spectra, sorted by size)</h1>
  <p class="all-link">
    <a href="{all_url}" target="_blank">&#9654; View all {n_total} representative spectra in the inspector</a>
  </p>
  <p>For each cluster: the {N_SAMPLE} spectra closest to the centre of mass in UMAP space.</p>
{sections_html}
{noise_html}
</body>
</html>
"""

    outpath = f"html/all_clusters_loa_{tag}.html"
    with open(outpath, "w") as fh:
        fh.write(html)
    shutil.copy(outpath, CFS_DIR / pathlib.Path(outpath).name)
    print(f"  Saved {outpath}  →  CFS")

print("\nAll batches done.")
