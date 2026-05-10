import numpy as np
import pandas as pd
import pathlib, shutil

NPZ_FILE = ("/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/"
            "outlier_umap_batches_test/outlier_umap_batch_0001.npz")
LABELS   = "data/cluster_labels.npy"
SPECPROD = "matterhorn"
BASE_URL = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra"
N_SAMPLE = 10
RNG_SEED = 42

print("Loading data...")
f      = np.load(NPZ_FILE)
labels = np.load(LABELS)
emb    = f["embedding"]

unique, counts = np.unique(labels[labels >= 0], return_counts=True)
# sort clusters by size descending
order  = np.argsort(-counts)
unique = unique[order]
counts = counts[order]

print(f"  {len(unique)} clusters, building HTML...")

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

# ── noise section ─────────────────────────────────────────────────────────────
noise_indices = np.where(labels == -1)[0]
rng           = np.random.default_rng(RNG_SEED)
noise_sample  = rng.choice(noise_indices, size=N_SAMPLE, replace=False)

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
      &nbsp;<a href="{noise_cluster_url}" target="_blank">[view {N_SAMPLE} in inspector]</a>
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
  <title>All HDBSCAN clusters — Matterhorn</title>
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
  <h1>HDBSCAN clusters — Matterhorn ({len(unique)} clusters, sorted by size)</h1>
  <p class="all-link">
    <a href="{all_url}" target="_blank">&#9654; View all {n_total} representative spectra in the inspector</a>
  </p>
  <p>For each cluster: the {N_SAMPLE} spectra closest to the centre of mass in UMAP space.</p>
{sections_html}
{noise_html}
</body>
</html>
"""

outpath = "html/all_clusters_matterhorn.html"
with open(outpath, "w") as fh:
    fh.write(html)
print(f"Saved {outpath}")

cfs_dir = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
cfs_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(outpath, cfs_dir / pathlib.Path(outpath).name)
print(f"Copied to {cfs_dir / pathlib.Path(outpath).name}")
