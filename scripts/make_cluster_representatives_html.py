import pandas as pd
import pathlib, shutil

REPS     = "data/cluster_representatives.csv"
SPECPROD = "matterhorn"
BASE_URL = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra/tiles"

df = pd.read_csv(REPS)

rows = ""
for _, r in df.iterrows():
    url = f"{BASE_URL}/{int(r['tileid'])}/{int(r['fiber'])}"
    rows += f"""
      <tr>
        <td>{int(r['cluster'])}</td>
        <td>{int(r['size']):,}</td>
        <td>{r['cx']:.2f}</td>
        <td>{r['cy']:.2f}</td>
        <td>{int(r['targetid'])}</td>
        <td>{int(r['tileid'])}</td>
        <td>{int(r['fiber'])}</td>
        <td><a href="{url}" target="_blank">inspector</a></td>
      </tr>"""

all_targetids = ",".join(str(int(t)) for t in df["targetid"])
all_url       = f"https://inspector.desi.lbl.gov/{SPECPROD}/spectra/{all_targetids}"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HDBSCAN cluster representatives — Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1200px; }}
    h1   {{ font-size: 1.4em; }}
    .all-link {{ margin-bottom: 1em; font-size: 1em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; cursor: pointer; user-select: none; }}
    th:hover {{ background: #ddd; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; }}
  </style>
  <script>
    function sortTable(col) {{
      const table = document.getElementById('tbl');
      const rows  = Array.from(table.tBodies[0].rows);
      const asc   = table.dataset.sortCol == col && table.dataset.sortDir == 'asc';
      rows.sort((a, b) => {{
        const va = a.cells[col].innerText;
        const vb = b.cells[col].innerText;
        const na = parseFloat(va), nb = parseFloat(vb);
        const cmp = isNaN(na) ? va.localeCompare(vb) : na - nb;
        return asc ? -cmp : cmp;
      }});
      rows.forEach(r => table.tBodies[0].appendChild(r));
      table.dataset.sortCol = col;
      table.dataset.sortDir = asc ? 'desc' : 'asc';
    }}
  </script>
</head>
<body>
  <h1>HDBSCAN cluster representatives — Matterhorn ({len(df)} clusters)</h1>
  <p class="all-link">
    <a href="{all_url}" target="_blank">&#9654; View all {len(df)} representative spectra in the inspector</a>
  </p>
  <p>
    One representative spectrum per cluster, selected as the point closest to
    the cluster centre of mass in the 2D UMAP embedding.
    Click column headers to sort.
  </p>
  <table id="tbl">
    <thead>
      <tr>
        <th onclick="sortTable(0)">Cluster</th>
        <th onclick="sortTable(1)">Size</th>
        <th onclick="sortTable(2)">UMAP x</th>
        <th onclick="sortTable(3)">UMAP y</th>
        <th onclick="sortTable(4)">TARGETID</th>
        <th onclick="sortTable(5)">TILEID</th>
        <th onclick="sortTable(6)">FIBER</th>
        <th>Inspector</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</body>
</html>
"""

outpath = "html/cluster_representatives_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath}")

cfs_dir = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
cfs_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(outpath, cfs_dir / pathlib.Path(outpath).name)
print(f"Copied to {cfs_dir / pathlib.Path(outpath).name}")
