"""
For each LAE target found in the Loa or Matterhorn UMAP batches, show the
LAE spectrum and its 10 closest UMAP neighbours within the same HDBSCAN cluster
(or within the full batch when no cluster labels are available).

Inputs:
  DR1_LAE_submitted_version.fits          -- LAE catalog (19,685 targets)
  Loa UMAP batches + cluster_labels_loa_{tag}.npy  (all 11 batches labelled)
  Matterhorn UMAP batches; cluster_labels.npy only for batch 0001

Outputs:
  html/lae_neighbors_loa.html
  html/lae_neighbors_matterhorn.html
"""
import numpy as np
import pandas as pd
import pathlib
import shutil
import fitsio

LAE_FILE  = "DR1_LAE_submitted_version.fits"
CFS_DIR   = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
N_NEIGH   = 10

PRODUCTIONS = {
    "loa": {
        "batch_dir":    pathlib.Path("/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/outlier_umap_batches"),
        "label_pattern": "data/cluster_labels_loa_{tag}.npy",
        "out_html":     "html/lae_neighbors_loa.html",
    },
    "matterhorn": {
        "batch_dir":    pathlib.Path("/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/outlier_umap_batches"),
        "label_pattern": None,   # handled per-batch below
        "out_html":     "html/lae_neighbors_matterhorn.html",
    },
}

MATTERHORN_LABELS = {
    "0001": "data/cluster_labels.npy",
}

pathlib.Path("html").mkdir(exist_ok=True)
CFS_DIR.mkdir(parents=True, exist_ok=True)

# ── load LAE catalog ──────────────────────────────────────────────────────────
lae_raw = fitsio.read(LAE_FILE, ext="INFO")
lae_ids = set(lae_raw["TARGETID"].astype(int))
lae_zlya = {int(r["TARGETID"]): float(r["Z_LYA"]) for r in lae_raw}
lae_prob = {int(r["TARGETID"]): float(r["PROB"]) for r in lae_raw}
print(f"LAE targets: {len(lae_ids)}")


def build_html(specprod, cfg):
    batch_dir = cfg["batch_dir"]
    base_url  = f"https://inspector.desi.lbl.gov/{specprod}/spectra"

    matches  = []
    sections = []

    for npz_path in sorted(batch_dir.glob("outlier_umap_batch_????.npz")):
        tag = npz_path.stem.split("_")[-1]
        try:
            f = np.load(npz_path)
        except PermissionError:
            print(f"  skipping {npz_path.name} (permission denied)")
            continue

        tids   = f["targetids"].astype(int)
        emb    = f["embedding"]
        tileids = f["tileids"].astype(int)
        fibers  = f["fibers"].astype(int)
        nights  = f["nights"].astype(int)

        # load cluster labels if available
        if specprod == "loa":
            label_path = f"data/cluster_labels_loa_{tag}.npy"
        else:
            label_path = MATTERHORN_LABELS.get(tag)

        if label_path and pathlib.Path(label_path).exists():
            labels = np.load(label_path)
            has_labels = True
        else:
            labels = None
            has_labels = False

        found_in_batch = [(i, tid) for i, tid in enumerate(tids) if tid in lae_ids]
        if not found_in_batch:
            continue
        print(f"  batch {tag}: {len(found_in_batch)} LAE(s) found")

        for idx, tid in found_in_batch:
            lae_xy = emb[idx]

            if has_labels:
                cluster = int(labels[idx])
                if cluster == -1:
                    pool = np.where(labels == -1)[0]
                else:
                    pool = np.where(labels == cluster)[0]
                cluster_label = str(cluster)
            else:
                pool = np.arange(len(tids))
                cluster_label = "n/a"

            pool = pool[pool != idx]   # exclude the LAE itself
            dists = np.linalg.norm(emb[pool] - lae_xy, axis=1)
            top_n = pool[np.argsort(dists)[:N_NEIGH]]

            neigh_tids   = [int(tids[j])   for j in top_n]
            neigh_tiles  = [int(tileids[j]) for j in top_n]
            neigh_fibers = [int(fibers[j])  for j in top_n]
            neigh_nights = [int(nights[j])  for j in top_n]
            neigh_dists  = [float(dists[np.where(pool == j)[0][0]]) for j in top_n]

            matches.append({
                "TARGETID":        tid,
                "TILEID":          int(tileids[idx]),
                "FIBER":           int(fibers[idx]),
                "batch":           tag,
                "hdbscan_cluster": cluster_label,
                "Z_LYA":           lae_zlya[tid],
                "PROB":            lae_prob[tid],
            })

            lae_url   = f"{base_url}/{tid}"
            all_ids   = [str(tid)] + [str(t) for t in neigh_tids]
            group_url = f"{base_url}/" + ",".join(all_ids)
            tile_url  = f"{base_url}/tiles/{int(tileids[idx])}/{int(fibers[idx])}"

            cluster_note = (f"HDBSCAN cluster {cluster_label}"
                            if has_labels else "no cluster labels — full batch")

            neigh_rows = ""
            for ntid, ntile, nfiber, nnight, ndist in zip(
                    neigh_tids, neigh_tiles, neigh_fibers, neigh_nights, neigh_dists):
                nurl = f"{base_url}/tiles/{ntile}/{nfiber}"
                neigh_rows += f"""
          <tr>
            <td>{ntid}</td>
            <td>{ntile}</td>
            <td>{nfiber}</td>
            <td>{nnight}</td>
            <td>{ndist:.4f}</td>
            <td><a href="{nurl}" target="_blank">inspector</a></td>
          </tr>"""

            sections.append(f"""
  <div class="lae-block">
    <h2>
      TARGETID {tid}
      &mdash; TILE {int(tileids[idx])} FIBER {int(fibers[idx])}
      &nbsp;<span class="meta">batch {tag} · {cluster_note}
      · Z_LYA={lae_zlya[tid]:.4f} · PROB={lae_prob[tid]:.3f}</span>
    </h2>
    <p>
      <a href="{lae_url}" target="_blank">[view LAE in inspector]</a>
      &nbsp;&nbsp;
      <a href="{tile_url}" target="_blank">[inspector via tile/fiber]</a>
      &nbsp;&nbsp;
      <a href="{group_url}" target="_blank">[view LAE + {N_NEIGH} neighbours in inspector]</a>
    </p>
    <table>
      <thead>
        <tr><th colspan="6">{N_NEIGH} closest UMAP neighbours ({cluster_note})</th></tr>
        <tr>
          <th>TARGETID</th><th>TILEID</th><th>FIBER</th>
          <th>NIGHT</th><th>UMAP dist</th><th>Inspector</th>
        </tr>
      </thead>
      <tbody>{neigh_rows}
      </tbody>
    </table>
  </div>""")

    if not matches:
        print(f"  No LAE matches found in {specprod}.")
        return

    # save CSV
    csv_path = f"data/lae_neighbors_{specprod}.csv"
    pd.DataFrame(matches).to_csv(csv_path, index=False)
    print(f"Saved {len(matches)} matches to {csv_path}")

    # sort sections by Z_LYA
    order = np.argsort([m["Z_LYA"] for m in matches])
    sections_html = "\n".join(sections[i] for i in order)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LAE neighbours in {specprod} UMAP batches</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1100px; }}
    h1   {{ font-size: 1.4em; }}
    h2   {{ font-size: 1.05em; margin-top: 2em; border-bottom: 1px solid #ccc;
            padding-bottom: 4px; }}
    .meta {{ color: #666; font-weight: normal; font-size: 0.88em; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 0.5em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 8px; text-align: left;
              font-size: 0.9em; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .lae-block {{ margin-bottom: 2.5em; }}
    a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <h1>LAE UMAP neighbours — {specprod} ({len(matches)} LAEs found)</h1>
  <p>
    {len(matches)} LAE targets from <em>DR1_LAE_submitted_version.fits</em>
    found in the {specprod} UMAP batches. For each: the {N_NEIGH} closest
    spectra in UMAP space within the same HDBSCAN cluster (or full batch when
    no labels are available). Sorted by Z_LYA.
  </p>
{sections_html}
</body>
</html>
"""

    out = cfg["out_html"]
    with open(out, "w") as fh:
        fh.write(html)
    shutil.copy(out, CFS_DIR / pathlib.Path(out).name)
    print(f"Saved {out}  →  CFS")


for specprod, cfg in PRODUCTIONS.items():
    print(f"\n=== {specprod} ===")
    build_html(specprod, cfg)
