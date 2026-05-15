import fitsio
import pandas as pd
import numpy as np
import pathlib
import shutil
import math

LAE_FILE = "DR1_LAE_submitted_version.fits"
LOA_FILE = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
MTH_FILE = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
CFS_DIR  = pathlib.Path("/global/cfs/cdirs/desi/users/forero/outliers")
GROUP_SIZE = 20

# Load LAE catalog with native byte order
lae = fitsio.read(LAE_FILE, ext="INFO")
lae_df = pd.DataFrame({col: np.array(lae[col], dtype=lae[col].dtype.newbyteorder("="))
                        for col in lae.dtype.names})

loa = pd.read_csv(LOA_FILE, usecols=["TARGETID", "TILEID", "FIBER"])
mth = pd.read_csv(MTH_FILE, usecols=["TARGETID", "TILEID", "FIBER"])

lae_ids      = set(lae_df["TARGETID"])
loa_ids      = set(loa["TARGETID"])
mth_ids      = set(mth["TARGETID"])
both         = lae_ids & loa_ids & mth_ids
loa_only_ids = (lae_ids & loa_ids) - mth_ids
mth_only_ids = (lae_ids & mth_ids) - loa_ids

print(f"Loa-only: {len(loa_only_ids)}  |  Matterhorn-only: {len(mth_only_ids)}  |  Both: {len(both)}")


def build_df(target_ids, outlier_df, tile_col, fiber_col):
    mask = lae_df["TARGETID"].isin(target_ids)
    df = lae_df[mask].copy().reset_index(drop=True)
    info = (outlier_df[outlier_df["TARGETID"].isin(target_ids)]
            .drop_duplicates("TARGETID")[["TARGETID", "TILEID", "FIBER"]]
            .rename(columns={"TILEID": tile_col, "FIBER": fiber_col}))
    df = df.merge(info, on="TARGETID", how="left")
    df = df.sort_values("Z_LYA").reset_index(drop=True)
    return df


def oii_snr_str(v):
    if pd.isna(v):
        return "—"
    return f"{v:.2f}"


def build_html(df, specprod, title, tile_col, fiber_col):
    base_url = f"https://inspector.desi.lbl.gov/{specprod}/spectra"
    n_groups = math.ceil(len(df) / GROUP_SIZE)
    sections = ""

    for g in range(n_groups):
        chunk = df.iloc[g * GROUP_SIZE:(g + 1) * GROUP_SIZE]
        group_ids = ",".join(str(int(t)) for t in chunk["TARGETID"])
        group_url = f"{base_url}/{group_ids}"
        g_start = g * GROUP_SIZE + 1
        g_end   = min((g + 1) * GROUP_SIZE, len(df))

        rows = ""
        for _, r in chunk.iterrows():
            tile_url = f"{base_url}/tiles/{int(r[tile_col])}/{int(r[fiber_col])}"
            rows += f"""
          <tr>
            <td>{int(r['TARGETID'])}</td>
            <td>{r['TARGET_RA']:.5f}</td>
            <td>{r['TARGET_DEC']:.5f}</td>
            <td>{r['Z_LYA']:.4f}</td>
            <td>{r['PROB']:.3f}</td>
            <td>{oii_snr_str(r['OII_SNR'])}</td>
            <td>{int(r[tile_col])}</td>
            <td>{int(r[fiber_col])}</td>
            <td><a href="{tile_url}" target="_blank">inspector</a></td>
          </tr>"""

        sections += f"""
  <div class="group">
    <h2>Group {g + 1} &mdash; targets {g_start}–{g_end}
      &nbsp;<a href="{group_url}" target="_blank">[view {len(chunk)} in inspector]</a>
    </h2>
    <table>
      <thead>
        <tr>
          <th>TARGETID</th>
          <th>RA</th>
          <th>Dec</th>
          <th>Z_LYA</th>
          <th>PROB</th>
          <th>OII_SNR</th>
          <th>TILEID</th>
          <th>FIBER</th>
          <th>Inspector</th>
        </tr>
      </thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>"""

    all_ids = ",".join(str(int(t)) for t in df["TARGETID"])
    all_url = f"{base_url}/{all_ids}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; max-width: 1200px; }}
    h1   {{ font-size: 1.4em; }}
    h2   {{ font-size: 1.1em; margin-top: 2em; border-top: 1px solid #ccc; padding-top: 0.6em; }}
    h2 a {{ font-size: 0.9em; }}
    p    {{ margin: 0.4em 0; }}
    .toc {{ margin: 1em 0; padding: 0.8em 1em; background: #f8f8f8; border: 1px solid #ddd; display: inline-block; }}
    .toc a {{ display: inline-block; margin: 2px 6px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 9px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>
    {len(df)} LAE targets from <em>DR1_LAE_submitted_version.fits</em> that are
    UMAP outliers in <strong>{specprod}</strong> but not in the other production.
    Sorted by Z_LYA. Groups of {GROUP_SIZE} for the inspector.
  </p>
  <p><a href="{all_url}" target="_blank">&#9654; View all {len(df)} in inspector</a></p>
  <div class="toc">
    Jump to group:
    {"".join(f'<a href="#g{g+1}">{g+1}</a>' for g in range(n_groups))}
  </div>
  {"  ".join(f'<a id="g{g+1}"></a>' for g in range(n_groups))}
{sections}
</body>
</html>
"""


pathlib.Path("html").mkdir(exist_ok=True)
CFS_DIR.mkdir(parents=True, exist_ok=True)

# Loa-only
df_loa = build_df(loa_only_ids, loa, "TILEID", "FIBER")
html_loa = build_html(df_loa, "loa", "LAE outliers — Loa only", "TILEID", "FIBER")
out_loa = "html/lae_outliers_loa_only.html"
with open(out_loa, "w") as f:
    f.write(html_loa)
shutil.copy(out_loa, CFS_DIR / pathlib.Path(out_loa).name)
print(f"Saved {out_loa}  ({len(df_loa)} targets, {math.ceil(len(df_loa)/GROUP_SIZE)} groups)")

# Matterhorn-only
df_mth = build_df(mth_only_ids, mth, "TILEID", "FIBER")
html_mth = build_html(df_mth, "matterhorn", "LAE outliers — Matterhorn only", "TILEID", "FIBER")
out_mth = "html/lae_outliers_matterhorn_only.html"
with open(out_mth, "w") as f:
    f.write(html_mth)
shutil.copy(out_mth, CFS_DIR / pathlib.Path(out_mth).name)
print(f"Saved {out_mth}  ({len(df_mth)} targets, {math.ceil(len(df_mth)/GROUP_SIZE)} groups)")
