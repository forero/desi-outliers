"""
For each HSC lens candidate found in the Loa UMAP batches, show the lens
spectrum and its 10 closest UMAP neighbours within the same HDBSCAN cluster.

Inputs:
  outlier_lenses_catalog.fits            — 67 IS_HSC=True lens TARGETIDs
  data/cluster_labels_loa_{tag}.npy      — HDBSCAN labels per batch
  Loa UMAP NPZ batches

Outputs:
  data/hsc_lenses_loa_matches.csv        — match table (all HSC in Loa batches)
  html/hsc_lenses_loa.html               — HTML report
"""
import numpy as np
import pandas as pd
import pathlib
import shutil
import fitsio

BATCH_DIR   = pathlib.Path("/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/outlier_umap_batches")
LENS_FITS   = pathlib.Path("/pscratch/sd/v/vtorresg/desi-lenses/rapids_10_batches/outlier_lenses_catalog.fits")
SPECPROD    = "loa"
BASE_URL    = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra"
N_NEIGH     = 10
CFS_DIR     = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")

pathlib.Path("html").mkdir(exist_ok=True)
CFS_DIR.mkdir(parents=True, exist_ok=True)

# ── load all IS_HSC=True lenses ───────────────────────────────────────────────
lens_cat = fitsio.read(str(LENS_FITS))
hsc_mask = lens_cat["IS_HSC"].astype(bool)
hsc_cat  = lens_cat[hsc_mask]
hsc_ids  = set(hsc_cat["TARGETID"].astype(int))
hsc_tile = {int(r["TARGETID"]): (int(r["TILE"]), int(r["FIBER"])) for r in hsc_cat}
print(f"IS_HSC targets in lens catalog: {len(hsc_ids)}")

# ── find lenses in each Loa batch and collect neighbours ─────────────────────
matches  = []   # rows for the CSV
sections = []   # HTML sections

for npz_path in sorted(BATCH_DIR.glob("outlier_umap_batch_????.npz")):
    tag = npz_path.stem.split("_")[-1]
    try:
        f = np.load(npz_path)
    except PermissionError:
        continue

    tids   = f["targetids"].astype(int)
    emb    = f["embedding"]
    nights = f["nights"].astype(int)
    labels = np.load(f"data/cluster_labels_loa_{tag}.npy")

    for i, tid in enumerate(tids):
        if tid not in hsc_ids:
            continue

        cluster = int(labels[i])
        lens_xy = emb[i]

        # neighbours: same cluster, excluding the lens itself
        if cluster == -1:
            cluster_mask = labels == -1
        else:
            cluster_mask = labels == cluster
        cluster_mask[i] = False          # exclude lens

        cluster_idx  = np.where(cluster_mask)[0]
        dists        = np.linalg.norm(emb[cluster_idx] - lens_xy, axis=1)
        top_n        = cluster_idx[np.argsort(dists)[:N_NEIGH]]

        neigh_tids   = [int(tids[j])   for j in top_n]
        neigh_tiles  = [int(f["tileids"][j]) for j in top_n]
        neigh_fibers = [int(f["fibers"][j])  for j in top_n]
        neigh_nights = [int(nights[j])        for j in top_n]
        neigh_dists  = [float(dists[np.where(cluster_idx == j)[0][0]]) for j in top_n]

        tile_lens, fiber_lens = hsc_tile[tid]

        matches.append({
            "TARGETID":       tid,
            "TILE":           tile_lens,
            "FIBER":          fiber_lens,
            "loa_batch":      tag,
            "hdbscan_cluster": cluster,
        })

        # inspector URL for lens alone
        lens_url  = f"{BASE_URL}/{tid}"
        # combined URL: lens + neighbours
        all_ids   = [str(tid)] + [str(t) for t in neigh_tids]
        group_url = f"{BASE_URL}/" + ",".join(all_ids)

        neigh_rows = ""
        for ntid, ntile, nfiber, nnight, ndist in zip(
                neigh_tids, neigh_tiles, neigh_fibers, neigh_nights, neigh_dists):
            tile_url = f"{BASE_URL}/tiles/{ntile}/{nfiber}"
            neigh_rows += f"""
          <tr>
            <td>{ntid}</td>
            <td>{ntile}</td>
            <td>{nfiber}</td>
            <td>{nnight}</td>
            <td>{ndist:.4f}</td>
            <td><a href="{tile_url}" target="_blank">inspector</a></td>
          </tr>"""

        sections.append(f"""
  <div class="lens-block">
    <h2>
      TARGETID {tid} &mdash; TILE {tile_lens} FIBER {fiber_lens}
      &nbsp;<span class="meta">Loa batch {tag} · HDBSCAN cluster {cluster}</span>
    </h2>
    <p>
      <a href="{lens_url}" target="_blank">[view lens in inspector]</a>
      &nbsp;&nbsp;
      <a href="{group_url}" target="_blank">[view lens + {N_NEIGH} neighbours in inspector]</a>
    </p>
    <table>
      <thead>
        <tr>
          <th colspan="6">Lens</th>
        </tr>
        <tr>
          <th>TARGETID</th><th>TILE</th><th>FIBER</th>
          <th colspan="2"></th><th>Inspector</th>
        </tr>
      </thead>
      <tbody>
        <tr class="lens-row">
          <td><strong>{tid}</strong></td>
          <td>{tile_lens}</td>
          <td>{fiber_lens}</td>
          <td colspan="2"></td>
          <td><a href="{lens_url}" target="_blank">inspector</a></td>
        </tr>
      </tbody>
    </table>
    <table style="margin-top:0.5em;">
      <thead>
        <tr>
          <th colspan="6">{N_NEIGH} closest neighbours in cluster {cluster} (UMAP distance)</th>
        </tr>
        <tr>
          <th>TARGETID</th><th>TILE</th><th>FIBER</th>
          <th>NIGHT</th><th>UMAP dist</th><th>Inspector</th>
        </tr>
      </thead>
      <tbody>{neigh_rows}
      </tbody>
    </table>
  </div>""")

# ── save CSV ──────────────────────────────────────────────────────────────────
csv_path = "data/hsc_lenses_loa_matches.csv"
pd.DataFrame(matches).to_csv(csv_path, index=False)
print(f"Saved {len(matches)} matches to {csv_path}")

# ── build HTML ────────────────────────────────────────────────────────────────
sections_html = "\n".join(sections)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HSC lens candidates in Loa UMAP batches</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1100px; }}
    h1   {{ font-size: 1.4em; }}
    h2   {{ font-size: 1.1em; margin-top: 2em; border-bottom: 1px solid #ccc;
            padding-bottom: 4px; }}
    .meta {{ color: #666; font-weight: normal; font-size: 0.9em; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 0.5em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 8px; text-align: left; font-size: 0.9em; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    tr.lens-row {{ background: #fffbe6; font-weight: bold; }}
    a  {{ color: #0066cc; }}
    .lens-block {{ margin-bottom: 2.5em; }}
  </style>
</head>
<body>
  <h1>HSC lens candidates found in Loa UMAP batches ({len(matches)} of {len(hsc_ids)})</h1>
  <p>
    For each lens: inspector link for the lens alone and combined with its
    {N_NEIGH} closest UMAP neighbours within the same HDBSCAN cluster.
  </p>
{sections_html}
</body>
</html>
"""

out_html = "html/hsc_lenses_loa.html"
with open(out_html, "w") as fh:
    fh.write(html)
shutil.copy(out_html, CFS_DIR / pathlib.Path(out_html).name)
print(f"Saved {out_html}  →  CFS")
