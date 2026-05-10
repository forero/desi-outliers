import numpy as np
import pandas as pd
import fitsio
from scipy.stats import beta

OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"


def clopper_pearson(k, n, alpha=0.05):
    lo = beta.ppf(alpha / 2,     k,     n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k)     if k < n else 1.0
    return lo, k / n, hi


def fmt(lo, mid, hi):
    return f"{mid*100:.2f}% [{lo*100:.2f}%, {hi*100:.2f}%]"


print("Reading outlier catalog...")
out = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
print(f"  {len(out):,} outliers")

print("Reading zcatalog...")
data = fitsio.read(ZCAT, ext="ZCATALOG",
                   columns=["TARGETID", "TILEID", "ZWARN", "SURVEY", "PROGRAM"])
zcat = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().view(data["TARGETID"].dtype.newbyteorder()),
    "TILEID":   data["TILEID"].byteswap().view(data["TILEID"].dtype.newbyteorder()),
    "ZWARN":    data["ZWARN"].byteswap().view(data["ZWARN"].dtype.newbyteorder()),
    "SURVEY":   [s.strip() for s in data["SURVEY"]],
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
})
print(f"  {len(zcat):,} zcatalog entries")

print("Merging...")
merged = out.merge(zcat, on=["TARGETID", "TILEID"], how="left")
n_unmatched = merged["ZWARN"].isna().sum()
print(f"  {len(merged):,} matched, {n_unmatched:,} unmatched (no zcatalog entry)")

# Restrict to main survey
main = merged[merged["SURVEY"] == "main"].copy()
print(f"  {len(main):,} main-survey outliers after merge")

print()
print("=" * 60)
for program in ["dark", "bright", "backup", "all"]:
    sub = main if program == "all" else main[main["PROGRAM"] == program]
    n    = len(sub)
    k    = int((sub["ZWARN"] != 0).sum())
    lo, mid, hi = clopper_pearson(k, n)
    label = program.capitalize()
    print(f"{label:8s}  N={n:>9,}  ZWARN!=0: {k:>7,}  fraction = {fmt(lo, mid, hi)}")
