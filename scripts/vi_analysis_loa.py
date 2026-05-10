"""
VI and ZWARN quality analysis for Loa outliers.
Produces:
  - Per-tile and aggregated VI fractions with Clopper-Pearson intervals
  - ZWARN != 0 fractions for the full Loa main-survey outlier catalog
"""
import numpy as np
import pandas as pd
import fitsio
from scipy.stats import beta

VI_FILE  = "data/vi_tiles_loa.csv"
OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"


def clopper_pearson(k, n, alpha=0.05):
    if n == 0:
        return np.nan, np.nan, np.nan
    lo  = beta.ppf(alpha / 2,     k,     n - k + 1) if k > 0 else 0.0
    hi  = beta.ppf(1 - alpha / 2, k + 1, n - k)     if k < n else 1.0
    return lo, k / n, hi


def fmt(lo, mid, hi, decimals=1):
    s = 100
    return f"{mid*s:.{decimals}f}% [{lo*s:.{decimals}f}%, {hi*s:.{decimals}f}%]"


# ── VI sample statistics ──────────────────────────────────────────────────────
print("=" * 60)
print("VI sample statistics")
print("=" * 60)

vi = pd.read_csv(VI_FILE)

print("\nPer-tile:")
for _, row in vi.iterrows():
    n, k_vi, k_zw = int(row["n_outliers"]), int(row["n_bad_vi"]), int(row["zwarn_neq_0"])
    print(f"\n  Tile {row['tileid']} ({row['program']}), N={n}")
    print(f"    VI problems   : {k_vi}/{n} = {fmt(*clopper_pearson(k_vi, n))}")
    print(f"    No VI problem : {n - k_vi} spectra")
    print(f"    zwarn != 0    : {k_zw}/{n} = {fmt(*clopper_pearson(k_zw, n))}")

print()
for program in ["dark", "bright", "all"]:
    sub  = vi if program == "all" else vi[vi["program"] == program]
    n    = int(sub["n_outliers"].sum())
    k_vi = int(sub["n_bad_vi"].sum())
    k_zw = int(sub["zwarn_neq_0"].sum())
    print("=" * 60)
    print(f"Aggregated: {program.capitalize()}  (N={n})")
    print("=" * 60)
    print(f"  VI problems   : {k_vi}/{n} = {fmt(*clopper_pearson(k_vi, n))}")
    print(f"  No VI problem : {n - k_vi} spectra")
    print(f"  zwarn != 0    : {k_zw}/{n} = {fmt(*clopper_pearson(k_zw, n))}")
    print()

# ── ZWARN fraction from full zcatalog ────────────────────────────────────────
print("=" * 60)
print("ZWARN != 0 in full Loa main-survey outlier catalog")
print("=" * 60)

print("\nReading outlier catalog...")
out = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
print(f"  {len(out):,} outliers")

print("Reading zcatalog...")
raw = fitsio.read(ZCAT, ext="ZCATALOG",
                  columns=["TARGETID", "TILEID", "ZWARN", "SURVEY", "PROGRAM"])
zcat = pd.DataFrame({
    "TARGETID": raw["TARGETID"].byteswap().view(raw["TARGETID"].dtype.newbyteorder()),
    "TILEID":   raw["TILEID"].byteswap().view(raw["TILEID"].dtype.newbyteorder()),
    "ZWARN":    raw["ZWARN"].byteswap().view(raw["ZWARN"].dtype.newbyteorder()),
    "SURVEY":   [s.strip() for s in raw["SURVEY"]],
    "PROGRAM":  [p.strip() for p in raw["PROGRAM"]],
})
print(f"  {len(zcat):,} zcatalog entries")

merged = out.merge(zcat, on=["TARGETID", "TILEID"], how="left")
main   = merged[merged["SURVEY"] == "main"].copy()
print(f"  {len(main):,} main-survey outliers after merge\n")

for program in ["dark", "bright", "backup", "dark+bright", "all"]:
    if program == "dark+bright":
        sub = main[main["PROGRAM"].isin(["dark", "bright"])]
    elif program == "all":
        sub = main
    else:
        sub = main[main["PROGRAM"] == program]
    n  = len(sub)
    k  = int((sub["ZWARN"] != 0).sum())
    lo, mid, hi = clopper_pearson(k, n)
    print(f"{program:12s}  N={n:>9,}  ZWARN!=0: {k:>7,}  {fmt(lo, mid, hi, decimals=2)}")
