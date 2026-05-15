import fitsio
import pandas as pd
import numpy as np
import pathlib
import shutil

LAE_FILE   = "DR1_LAE_submitted_version.fits"
LOA_FILE   = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
MTH_FILE   = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
OUT_HTML   = "html/lae_outliers_loa_matterhorn.html"
CFS_DIR    = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")

LOA_URL = "https://inspector.desi.lbl.gov/loa/spectra/tiles"
MTH_URL = "https://inspector.desi.lbl.gov/matterhorn/spectra/tiles"

# Load LAE catalog with native byte order
lae = fitsio.read(LAE_FILE, ext="INFO")
lae_df = pd.DataFrame({col: np.array(lae[col], dtype=lae[col].dtype.newbyteorder("="))
                        for col in lae.dtype.names})

# Load outlier catalogs
loa = pd.read_csv(LOA_FILE, usecols=["TARGETID", "TILEID", "FIBER"])
mth = pd.read_csv(MTH_FILE, usecols=["TARGETID", "TILEID", "FIBER"])

# Find the 34 TARGETIDs in both productions
both = set(lae_df["TARGETID"]) & set(loa["TARGETID"]) & set(mth["TARGETID"])

mask = lae_df["TARGETID"].isin(both)
df = lae_df[mask].copy().reset_index(drop=True)

# Attach Loa tile/fiber (first occurrence per TARGETID)
loa_info = loa[loa["TARGETID"].isin(both)].drop_duplicates("TARGETID")[["TARGETID", "TILEID", "FIBER"]]
loa_info = loa_info.rename(columns={"TILEID": "LOA_TILEID", "FIBER": "LOA_FIBER"})

mth_info = mth[mth["TARGETID"].isin(both)].drop_duplicates("TARGETID")[["TARGETID", "TILEID", "FIBER"]]
mth_info = mth_info.rename(columns={"TILEID": "MTH_TILEID", "FIBER": "MTH_FIBER"})

df = df.merge(loa_info, on="TARGETID", how="left")
df = df.merge(mth_info, on="TARGETID", how="left")
df = df.sort_values("Z_LYA").reset_index(drop=True)

# Build "view all" links
all_ids = ",".join(str(int(t)) for t in df["TARGETID"])
all_loa_url = f"https://inspector.desi.lbl.gov/loa/spectra/{all_ids}"
all_mth_url = f"https://inspector.desi.lbl.gov/matterhorn/spectra/{all_ids}"

def oii_snr_str(v):
    if pd.isna(v):
        return "—"
    return f"{v:.2f}"

rows = ""
for _, r in df.iterrows():
    loa_url = f"{LOA_URL}/{int(r['LOA_TILEID'])}/{int(r['LOA_FIBER'])}"
    mth_url = f"{MTH_URL}/{int(r['MTH_TILEID'])}/{int(r['MTH_FIBER'])}"
    rows += f"""
      <tr>
        <td>{int(r['TARGETID'])}</td>
        <td>{r['TARGET_RA']:.5f}</td>
        <td>{r['TARGET_DEC']:.5f}</td>
        <td>{r['Z_LYA']:.4f}</td>
        <td>{r['PROB']:.3f}</td>
        <td>{oii_snr_str(r['OII_SNR'])}</td>
        <td>{int(r['LOA_TILEID'])}</td>
        <td>{int(r['LOA_FIBER'])}</td>
        <td>{int(r['MTH_TILEID'])}</td>
        <td>{int(r['MTH_FIBER'])}</td>
        <td><a href="{loa_url}" target="_blank">Loa</a></td>
        <td><a href="{mth_url}" target="_blank">Matterhorn</a></td>
      </tr>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LAE outliers in both Loa and Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1400px; }}
    h1   {{ font-size: 1.4em; }}
    p    {{ margin: 0.4em 0; }}
    .all-links {{ margin-bottom: 1em; }}
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
        const na = parseFloat(va.replace('—','NaN')), nb = parseFloat(vb.replace('—','NaN'));
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
  <h1>LAE outliers in both Loa and Matterhorn ({len(df)} targets)</h1>
  <p>
    These {len(df)} targets appear in the DR1 LAE catalog
    (<em>DR1_LAE_submitted_version.fits</em>) and are flagged as UMAP outliers
    in <strong>both</strong> the Loa and Matterhorn spectroscopic productions.
    Table is sorted by Lya redshift. Click column headers to re-sort.
  </p>
  <div class="all-links">
    <a href="{all_loa_url}" target="_blank">&#9654; View all {len(df)} in Loa inspector</a>
    &nbsp;|&nbsp;
    <a href="{all_mth_url}" target="_blank">&#9654; View all {len(df)} in Matterhorn inspector</a>
  </div>
  <table id="tbl">
    <thead>
      <tr>
        <th onclick="sortTable(0)">TARGETID</th>
        <th onclick="sortTable(1)">RA</th>
        <th onclick="sortTable(2)">Dec</th>
        <th onclick="sortTable(3)">Z_LYA</th>
        <th onclick="sortTable(4)">PROB</th>
        <th onclick="sortTable(5)">OII_SNR</th>
        <th onclick="sortTable(6)">Loa TILEID</th>
        <th onclick="sortTable(7)">Loa FIBER</th>
        <th onclick="sortTable(8)">MTH TILEID</th>
        <th onclick="sortTable(9)">MTH FIBER</th>
        <th>Inspector (Loa)</th>
        <th>Inspector (MTH)</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</body>
</html>
"""

pathlib.Path("html").mkdir(exist_ok=True)
with open(OUT_HTML, "w") as f:
    f.write(html)
print(f"Saved {OUT_HTML}")

CFS_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy(OUT_HTML, CFS_DIR / pathlib.Path(OUT_HTML).name)
print(f"Copied to {CFS_DIR / pathlib.Path(OUT_HTML).name}")
