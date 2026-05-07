import numpy as np
import pandas as pd
import fitsio

ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS_LOA = "/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv"
OUTLIERS_MAT = "/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv"
TILES_LOA    = "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv"
TILES_MAT    = "/global/cfs/cdirs/desi/spectro/redux/daily/tiles-daily.csv"

TARGETS = {
    "LRG": "dark",
    "BGS": "bright",
}

PRODUCTIONS = {
    "Loa":        OUTLIERS_LOA,
    "Matterhorn": OUTLIERS_MAT,
}

TILES = {
    "Loa":        TILES_LOA,
    "Matterhorn": TILES_MAT,
}

print("Reading zcatalog...")
data = fitsio.read(ZCAT, ext="ZCATALOG", columns=["TARGETID", "TILEID", "PROGRAM", "FIBER"])
df_zcat = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().newbyteorder(),
    "TILEID":   data["TILEID"].byteswap().newbyteorder(),
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
    "FIBER":    data["FIBER"].byteswap().newbyteorder(),
})

fibers = np.arange(5000)

# pre-compute total targets per fiber per program from Loa zcatalog
n_total_by_program = {}
for label, program in TARGETS.items():
    sub = df_zcat[df_zcat["PROGRAM"] == program]
    n_total_by_program[label] = sub.groupby("FIBER").size().reindex(fibers, fill_value=0).values

# compute outlier fractions per fiber per (production, target class)
results = {}  # key: (prod, label) -> dict fiber -> fraction

for prod, outlier_path in PRODUCTIONS.items():
    print(f"Reading outliers for {prod}...")
    tiles = pd.read_csv(TILES[prod], usecols=["TILEID", "PROGRAM"])
    out = pd.read_csv(outlier_path, usecols=["TARGETID", "TILEID", "FIBER"])
    out = out.merge(tiles, on="TILEID", how="left")

    for label, program in TARGETS.items():
        sub = out[out["PROGRAM"] == program]
        n_out = sub.groupby("FIBER").size().reindex(fibers, fill_value=0).values
        n_tot = n_total_by_program[label]
        frac  = np.where(n_tot > 0, n_out / n_tot, np.nan)
        results[(prod, label)] = frac

# find high-outlier fibers per petal (mean + 3 sigma within petal)
sections = []
for label in TARGETS:
    for prod in PRODUCTIONS:
        frac = results[(prod, label)]
        high_fibers = []
        for petal in range(10):
            sl = slice(petal * 500, (petal + 1) * 500)
            f_petal = frac[sl]
            valid = np.isfinite(f_petal)
            if valid.sum() < 2:
                continue
            mean = f_petal[valid].mean()
            std  = f_petal[valid].std()
            threshold = mean + 3 * std
            above = np.where(valid & (f_petal > threshold))[0]
            for idx in above:
                fiber = petal * 500 + idx
                high_fibers.append({
                    "Petal":     petal,
                    "Fiber":     fiber,
                    "Fraction":  f_petal[idx],
                    "Mean":      mean,
                    "Std":       std,
                    "Threshold": threshold,
                    "Nsigma":    (f_petal[idx] - mean) / std,
                })
        sections.append((label, prod, high_fibers))
        print(f"{label} {prod}: {len(high_fibers)} fibers above mean+3sigma")

# render HTML
def make_table(rows, label, prod):
    if not rows:
        return f"<p>No fibers above mean+3&sigma; for {label} {prod}.</p>"
    header = "<tr><th>Petal</th><th>Fiber</th><th>Outlier fraction</th><th>Petal mean</th><th>Petal std</th><th>N&sigma; above mean</th></tr>"
    body = ""
    for r in sorted(rows, key=lambda x: (-x["Petal"], -x["Fraction"])):
        body += (f"<tr><td>{r['Petal']}</td><td>{r['Fiber']}</td>"
                 f"<td>{r['Fraction']:.4f}</td><td>{r['Mean']:.4f}</td>"
                 f"<td>{r['Std']:.4f}</td><td>{r['Nsigma']:.1f}</td></tr>")
    return f"<table><thead>{header}</thead><tbody>{body}</tbody></table>"

section_html = ""
for label, prod, rows in sections:
    section_html += f"<h2>{label} — {prod}</h2>\n"
    section_html += f"<p>{len(rows)} fibers with outlier fraction &gt; mean + 3&sigma; (per petal)</p>\n"
    section_html += make_table(rows, label, prod) + "\n"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>High outlier fraction fibers — Loa &amp; Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; }}
    h1 {{ font-size: 1.4em; }}
    h2 {{ font-size: 1.2em; margin-top: 2em; border-bottom: 1px solid #ccc; }}
    table {{ border-collapse: collapse; margin-bottom: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 10px; text-align: right; }}
    th {{ background: #f0f0f0; text-align: center; }}
    tr:nth-child(even) {{ background: #fafafa; }}
  </style>
</head>
<body>
  <h1>Fibers with outlier fraction &gt; mean + 3&sigma; per petal</h1>
  <p>Denominator: total targets per fiber from the Loa zcatalog (used for both productions).</p>
  {section_html}
</body>
</html>
"""

outpath = "high_outlier_fibers_loa_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath}")
