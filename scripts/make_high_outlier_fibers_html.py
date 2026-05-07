import numpy as np
import pandas as pd

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

fibers = np.arange(5000)

# compute raw outlier counts per fiber per (production, target class)
results = {}  # key: (prod, label) -> array of counts per fiber

for prod, outlier_path in PRODUCTIONS.items():
    print(f"Reading outliers for {prod}...")
    tiles = pd.read_csv(TILES[prod], usecols=["TILEID", "PROGRAM"])
    out = pd.read_csv(outlier_path, usecols=["TILEID", "FIBER"])
    out = out.merge(tiles, on="TILEID", how="left")

    for label, program in TARGETS.items():
        sub = out[out["PROGRAM"] == program]
        counts = sub.groupby("FIBER").size().reindex(fibers, fill_value=0).values.astype(float)
        results[(prod, label)] = counts

# find high-outlier fibers per petal (mean + 3 sigma within petal)
sections = []
for label in TARGETS:
    for prod in PRODUCTIONS:
        counts = results[(prod, label)]
        high_fibers = []
        for petal in range(10):
            sl = slice(petal * 500, (petal + 1) * 500)
            c_petal = counts[sl]
            mean = c_petal.mean()
            std  = c_petal.std()
            threshold = mean + 3 * std
            above = np.where(c_petal > threshold)[0]
            for idx in above:
                fiber = petal * 500 + idx
                high_fibers.append({
                    "Petal":   petal,
                    "Fiber":   fiber,
                    "Count":   int(c_petal[idx]),
                    "Mean":    mean,
                    "Std":     std,
                    "Nsigma":  (c_petal[idx] - mean) / std,
                })
        sections.append((label, prod, high_fibers))
        print(f"{label} {prod}: {len(high_fibers)} fibers above mean+3sigma")

# render HTML
def make_table(rows, label, prod):
    if not rows:
        return f"<p>No fibers above mean+3&sigma; for {label} {prod}.</p>"
    header = "<tr><th>Petal</th><th>Fiber</th><th>Outlier count</th><th>Petal mean</th><th>Petal std</th><th>N&sigma; above mean</th></tr>"
    body = ""
    for r in sorted(rows, key=lambda x: (-x["Petal"], -x["Count"])):
        body += (f"<tr><td>{r['Petal']}</td><td>{r['Fiber']}</td>"
                 f"<td>{r['Count']}</td><td>{r['Mean']:.1f}</td>"
                 f"<td>{r['Std']:.1f}</td><td>{r['Nsigma']:.1f}</td></tr>")
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
  <p>Selection: fibers with raw outlier count &gt; mean + 3&sigma; within each petal.</p>
  {section_html}
</body>
</html>
"""

outpath = "high_outlier_fibers_loa_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath}")
