import pandas as pd

loa = pd.read_csv('/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv')
mat = pd.read_csv('/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv')

tiles_loa = pd.read_csv('/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv', usecols=['TILEID','PROGRAM'])
tiles_mat = pd.read_csv('/global/cfs/cdirs/desi/spectro/redux/daily/tiles-daily.csv', usecols=['TILEID','PROGRAM'])

loa = loa.merge(tiles_loa, on='TILEID', how='left')
mat = mat.merge(tiles_mat, on='TILEID', how='left')

sl = loa[loa['PROGRAM'] == 'dark']
sm = mat[mat['PROGRAM'] == 'dark']

keys_l = set(zip(sl['TARGETID'], sl['FIBER'], sl['TILEID']))
keys_m = set(zip(sm['TARGETID'], sm['FIBER'], sm['TILEID']))
common = keys_l & keys_m

df = pd.DataFrame(list(common), columns=['TARGETID', 'FIBER', 'TILEID'])
counts = df['TILEID'].value_counts().reset_index()
counts.columns = ['TILEID', 'N_COMMON']
counts = counts.sort_values('N_COMMON', ascending=False).reset_index(drop=True)

# build fiber lists per tile
fiber_lists = df.groupby('TILEID')['FIBER'].apply(lambda x: ','.join(str(f) for f in sorted(x))).to_dict()

BASE_URL = "https://inspector.desi.lbl.gov/matterhorn/spectra/tiles"

rows = []
for _, row in counts.iterrows():
    tileid = int(row['TILEID'])
    n = int(row['N_COMMON'])
    fibers = fiber_lists[tileid]
    url = f"{BASE_URL}/{tileid}/{fibers}"
    rows.append(f"""
      <tr>
        <td>{tileid}</td>
        <td>{n}</td>
        <td><a href="{url}" target="_blank">{url}</a></td>
      </tr>""")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dark outliers common to Loa and Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; }}
    h1 {{ font-size: 1.4em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; cursor: pointer; user-select: none; }}
    th:hover {{ background: #ddd; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; word-break: break-all; }}
  </style>
  <script>
    function sortTable(col) {{
      const table = document.getElementById('tbl');
      const rows = Array.from(table.tBodies[0].rows);
      const asc = table.dataset.sortCol == col && table.dataset.sortDir == 'asc';
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
  <h1>Dark outliers common to Loa and Matterhorn ({len(counts):,} tiles)</h1>
  <p>Sorted by number of common outliers (descending). Click column headers to re-sort.</p>
  <table id="tbl">
    <thead>
      <tr>
        <th onclick="sortTable(0)">TILEID</th>
        <th onclick="sortTable(1)">N common outliers</th>
        <th>Inspector link</th>
      </tr>
    </thead>
    <tbody>{''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

import shutil, pathlib

outpath = "html/dark_common_outliers_loa_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath} ({len(counts)} tiles)")

cfs_dir = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
cfs_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(outpath, cfs_dir / pathlib.Path(outpath).name)
print(f"Copied to {cfs_dir / pathlib.Path(outpath).name}")
