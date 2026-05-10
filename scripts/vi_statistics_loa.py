import pandas as pd
import numpy as np
from scipy.stats import beta

VI_FILE = "data/vi_tiles_loa.csv"


def clopper_pearson(k, n, alpha=0.05):
    """Return (lo, mid, hi) Clopper-Pearson interval for k successes in n trials."""
    if n == 0:
        return np.nan, np.nan, np.nan
    lo = beta.ppf(alpha / 2,     k,     n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k)     if k < n else 1.0
    mid = k / n
    return lo, mid, hi


def fmt(lo, mid, hi, pct=True):
    scale = 100 if pct else 1
    return f"{mid*scale:.1f}% [{lo*scale:.1f}%, {hi*scale:.1f}%]"


df = pd.read_csv(VI_FILE)

print("=" * 60)
print("Per-tile results")
print("=" * 60)
for _, row in df.iterrows():
    n   = int(row["n_outliers"])
    k_vi   = int(row["n_bad_vi"])
    k_zw   = int(row["zwarn_neq_0"])
    n_good = n - k_vi

    lo_vi, mid_vi, hi_vi = clopper_pearson(k_vi, n)
    lo_zw, mid_zw, hi_zw = clopper_pearson(k_zw, n)

    print(f"\n  Tile {row['tileid']} ({row['program']}), N={n}")
    print(f"    VI problems      : {k_vi}/{n} = {fmt(lo_vi, mid_vi, hi_vi)}")
    print(f"    No VI problem    : {n_good} spectra")
    print(f"    zwarn != 0       : {k_zw}/{n} = {fmt(lo_zw, mid_zw, hi_zw)}")

print()
for program in ["dark", "bright", "all"]:
    sub = df if program == "all" else df[df["program"] == program]
    n      = int(sub["n_outliers"].sum())
    k_vi   = int(sub["n_bad_vi"].sum())
    k_zw   = int(sub["zwarn_neq_0"].sum())
    n_good = n - k_vi

    lo_vi, mid_vi, hi_vi = clopper_pearson(k_vi, n)
    lo_zw, mid_zw, hi_zw = clopper_pearson(k_zw, n)

    label = program.capitalize()
    print("=" * 60)
    print(f"Aggregated: {label}  (N={n})")
    print("=" * 60)
    print(f"  VI problems   : {k_vi}/{n} = {fmt(lo_vi, mid_vi, hi_vi)}")
    print(f"  No VI problem : {n_good} spectra")
    print(f"  zwarn != 0    : {k_zw}/{n} = {fmt(lo_zw, mid_zw, hi_zw)}")
    print()
