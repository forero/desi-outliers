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
results = {}

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
high_sets = {}
sections = []
for label in TARGETS:
    for prod in PRODUCTIONS:
        counts = results[(prod, label)]
        high_fibers = []
        fiber_set = set()
        for petal in range(10):
            sl = slice(petal * 500, (petal + 1) * 500)
            c_petal = counts[sl]
            mean = c_petal.mean()
            std  = c_petal.std()
            above = np.where(c_petal > mean + 3 * std)[0]
            for idx in above:
                fiber = petal * 500 + idx
                fiber_set.add(fiber)
                high_fibers.append({
                    "Petal":  petal,
                    "Fiber":  fiber,
                    "Count":  int(c_petal[idx]),
                    "Mean":   mean,
                    "Std":    std,
                    "Nsigma": (c_petal[idx] - mean) / std,
                })
        high_sets[(prod, label)] = fiber_set
        sections.append((label, prod, high_fibers))
        print(f"{label} {prod}: {len(high_fibers)} fibers above mean+3sigma")

# cross-comparisons
def overlap_table(a_key, b_key, a_label, b_label):
    a, b = high_sets[a_key], high_sets[b_key]
    rows = [
        (f"{a_label} only", sorted(a - b)),
        ("Common",           sorted(a & b)),
        (f"{b_label} only", sorted(b - a)),
    ]
    header = "<tr><th>Category</th><th>N</th><th>Fibers</th></tr>"
    body = "".join(
        f"<tr><td>{cat}</td><td>{len(fs)}</td><td>{', '.join(str(f) for f in fs) or '—'}</td></tr>"
        for cat, fs in rows
    )
    return f"<table><thead>{header}</thead><tbody>{body}</tbody></table>"

all_four = high_sets[("Loa","LRG")] & high_sets[("Loa","BGS")] & \
           high_sets[("Matterhorn","LRG")] & high_sets[("Matterhorn","BGS")]

cross_html = ""

cross_html += "<h2>Cross-comparison: LRG vs BGS (same specprod)</h2>\n"
for prod in PRODUCTIONS:
    cross_html += f"<h3>{prod}</h3>\n"
    cross_html += overlap_table((prod,"LRG"), (prod,"BGS"), "LRG", "BGS")

cross_html += "<h2>Cross-comparison: Loa vs Matterhorn (same tracer)</h2>\n"
for label in TARGETS:
    cross_html += f"<h3>{label}</h3>\n"
    cross_html += overlap_table(("Loa",label), ("Matterhorn",label), "Loa", "Matterhorn")

cross_html += "<h2>Common to all four (LRG+BGS &times; Loa+Matterhorn)</h2>\n"
cross_html += f"<p><strong>{len(all_four)} fibers</strong> flagged in every combination: "
cross_html += ", ".join(f"<strong>{f}</strong>" for f in sorted(all_four)) + "</p>\n"
cross_html += f"<p>Petals: { ', '.join(str(f//500) for f in sorted(all_four)) }</p>\n"

# per-section tables
def make_table(rows):
    if not rows:
        return "<p>No fibers above threshold.</p>"
    header = "<tr><th>Petal</th><th>Fiber</th><th>Outlier count</th><th>Petal mean</th><th>Petal std</th><th>N&sigma;</th></tr>"
    body = "".join(
        f"<tr><td>{r['Petal']}</td><td>{r['Fiber']}</td><td>{r['Count']}</td>"
        f"<td>{r['Mean']:.1f}</td><td>{r['Std']:.1f}</td><td>{r['Nsigma']:.1f}</td></tr>"
        for r in sorted(rows, key=lambda x: (-x["Petal"], -x["Count"]))
    )
    return f"<table><thead>{header}</thead><tbody>{body}</tbody></table>"

section_html = ""
for label, prod, rows in sections:
    section_html += f"<h2>{label} — {prod}</h2>\n"
    section_html += f"<p>{len(rows)} fibers with raw outlier count &gt; mean + 3&sigma; per petal</p>\n"
    section_html += make_table(rows) + "\n"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>High outlier fibers — Loa &amp; Matterhorn</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; }}
    h1 {{ font-size: 1.4em; }}
    h2 {{ font-size: 1.2em; margin-top: 2em; border-bottom: 1px solid #ccc; }}
    h3 {{ font-size: 1.0em; margin-top: 1em; }}
    table {{ border-collapse: collapse; margin-bottom: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 10px; text-align: right; }}
    th {{ background: #f0f0f0; text-align: center; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    td:first-child {{ text-align: left; }}
  </style>
</head>
<body>
  <h1>Fibers with raw outlier count &gt; mean + 3&sigma; per petal</h1>
  <p>Selection: raw outlier count &gt; mean + 3&sigma; within each petal of 500 fibers.</p>

  {cross_html}

  <h1>Individual tables by tracer and specprod</h1>
  {section_html}
</body>
</html>
"""

outpath = "html/high_outlier_fibers_loa_matterhorn.html"
with open(outpath, "w") as f:
    f.write(html)
print(f"Saved {outpath}")
