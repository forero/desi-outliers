import pandas as pd
import numpy as np
import shutil, pathlib

LOA_OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
MAT_OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
LOA_TILES    = "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv"
MAT_TILES    = "/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv"

print("Reading outliers...")
loa = pd.read_csv(LOA_OUTLIERS)
mat = pd.read_csv(MAT_OUTLIERS)

print("Reading tiles...")
tiles_loa = pd.read_csv(LOA_TILES, usecols=["TILEID", "PROGRAM", "SURVEY"])
tiles_mat = pd.read_csv(MAT_TILES, usecols=["TILEID", "PROGRAM", "SURVEY"])

loa_tileids = set(loa["TILEID"].unique())

# Loa: all tiles in Loa, main survey only
loa_full = loa.merge(tiles_loa, on="TILEID", how="left")
loa_full = loa_full[loa_full["SURVEY"] == "main"]

# Matterhorn: only tiles whose TILEID is not in Loa, main survey only
mat_not_loa = mat[~mat["TILEID"].isin(loa_tileids)].merge(tiles_mat, on="TILEID", how="left")
mat_not_loa = mat_not_loa[mat_not_loa["SURVEY"] == "main"]

print(f"Loa tiles: {loa['TILEID'].nunique():,}")
print(f"Matterhorn tiles not in Loa: {mat_not_loa['TILEID'].nunique():,}")


def select_near_mean(df, program, n=3, seed=42):
    sub = df[df["PROGRAM"] == program]
    counts = sub.groupby("TILEID").size().reset_index(name="N_OUTLIERS")
    mean_val = counts["N_OUTLIERS"].mean()
    selected = counts.sample(n=n, random_state=seed).sort_values("N_OUTLIERS").reset_index(drop=True)
    return selected, mean_val


def build_rows(df_full, selected, specprod, program):
    fiber_map = (
        df_full[df_full["PROGRAM"] == program]
        .groupby("TILEID")["FIBER"]
        .apply(lambda x: ",".join(str(f) for f in sorted(x)))
        .to_dict()
    )
    rows = []
    for _, row in selected.iterrows():
        tileid = int(row["TILEID"])
        n      = int(row["N_OUTLIERS"])
        fibers = fiber_map.get(tileid, "")
        url    = f"https://inspector.desi.lbl.gov/{specprod}/spectra/tiles/{tileid}/{fibers}"
        rows.append((tileid, n, url))
    return rows


sections = [
    ("Loa", loa_full, "loa"),
    ("Matterhorn (tiles not in Loa)", mat_not_loa, "matterhorn"),
]

html_sections = ""
for label, df, specprod in sections:
    html_sections += f'  <h2>{label}</h2>\n'
    for program in ["dark", "bright"]:
        selected, mean_val = select_near_mean(df, program, n=3)
        rows = build_rows(df, selected, specprod, program)
        print(f"{label} / {program}: mean={mean_val:.1f}, selected TILEIDs={[r[0] for r in rows]}")

        row_html = ""
        for tileid, n, url in rows:
            row_html += f"""
      <tr>
        <td>{tileid}</td>
        <td>{n}</td>
        <td><a href="{url}" target="_blank">{url}</a></td>
      </tr>"""

        html_sections += f"""
  <h3>{program.capitalize()} program &mdash; mean = {mean_val:.1f} outliers/tile</h3>
  <table>
    <thead>
      <tr><th>TILEID</th><th>N outliers</th><th>Inspector link</th></tr>
    </thead>
    <tbody>{row_html}
    </tbody>
  </table>
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mean-outlier tiles: Loa and Matterhorn-only</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1200px; }}
    h1   {{ font-size: 1.5em; }}
    h2   {{ font-size: 1.2em; margin-top: 2em; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
    h3   {{ font-size: 1.0em; color: #444; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; word-break: break-all; }}
  </style>
</head>
<body>
  <h1>Tiles near mean outlier count</h1>
  <p>
    <b>Loa</b>: all tiles in the Loa outlier catalog.<br>
    <b>Matterhorn (tiles not in Loa)</b>: tiles whose TILEID appears in Matterhorn but not in Loa.<br>
    Three tiles per program selected as the closest to the mean outlier count per tile.
  </p>
{html_sections}
</body>
</html>
"""

outpath = "html/mean_tiles_loa_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath}")

cfs_dir = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
cfs_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(outpath, cfs_dir / pathlib.Path(outpath).name)
print(f"Copied to {cfs_dir / pathlib.Path(outpath).name}")
