import numpy as np
import pandas as pd
import pathlib, shutil

NPZ_FILE   = ("/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/"
              "outlier_umap_batches_test/outlier_umap_batch_0001.npz")
LABELS     = "data/cluster_labels.npy"
SPECPROD   = "matterhorn"
BASE_URL   = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra/tiles"
N_SAMPLE   = 10
SEED       = 42

print("Loading data...")
f      = np.load(NPZ_FILE)
labels = np.load(LABELS)

# find the largest cluster
unique, counts = np.unique(labels[labels >= 0], return_counts=True)
largest_cid    = unique[counts.argmax()]
largest_size   = counts.max()
print(f"Largest cluster: {largest_cid}  ({largest_size:,} points)")

# random sample of N_SAMPLE points from that cluster
rng      = np.random.default_rng(SEED)
indices  = np.where(labels == largest_cid)[0]
sampled  = rng.choice(indices, size=N_SAMPLE, replace=False)
sampled  = sorted(sampled)

rows = ""
all_targetids = []
for idx in sampled:
    targetid = int(f["targetids"][idx])
    tileid   = int(f["tileids"][idx])
    fiber    = int(f["fibers"][idx])
    night    = int(f["nights"][idx])
    url      = f"{BASE_URL}/{tileid}/{fiber}"
    all_targetids.append(str(targetid))
    rows += f"""
      <tr>
        <td>{targetid}</td>
        <td>{tileid}</td>
        <td>{fiber}</td>
        <td>{night}</td>
        <td><a href="{url}" target="_blank">inspector</a></td>
      </tr>"""

all_url = (f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra/"
           + ",".join(all_targetids))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Largest HDBSCAN cluster — Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 900px; }}
    h1   {{ font-size: 1.4em; }}
    .all-link {{ margin-bottom: 1em; font-size: 1em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <h1>Largest HDBSCAN cluster (cluster {largest_cid}, {largest_size:,} spectra) — Matterhorn</h1>
  <p class="all-link">
    <a href="{all_url}" target="_blank">&#9654; View all {N_SAMPLE} sampled spectra in the inspector</a>
  </p>
  <p>
    {N_SAMPLE} randomly selected spectra (seed={SEED}) from the largest cluster
    of {largest_size:,} points.
  </p>
  <table>
    <thead>
      <tr>
        <th>TARGETID</th>
        <th>TILEID</th>
        <th>FIBER</th>
        <th>NIGHT</th>
        <th>Inspector</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</body>
</html>
"""

outpath = "html/largest_cluster_matterhorn.html"
with open(outpath, "w") as fh:
    fh.write(html)
print(f"Saved {outpath}")

cfs_dir = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
cfs_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(outpath, cfs_dir / pathlib.Path(outpath).name)
print(f"Copied to {cfs_dir / pathlib.Path(outpath).name}")
