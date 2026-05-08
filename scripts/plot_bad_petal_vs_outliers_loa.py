import numpy as np
import pandas as pd
import fitsio
import matplotlib.pyplot as plt

ZCAT     = "/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits"
OUTLIERS = "/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv"
TILES    = "/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv"
BAD_FILE = "/global/cfs/cdirs/desi/survey/catalogs/DA2/LSS/loa-v1/lrg_bad_per_petal-night.txt"

# parse bad (night, petal) pairs
bad_set = set()
with open(BAD_FILE) as f:
    for line in f:
        parts = line.split()
        night = int(parts[0])
        for p in parts[1:]:
            bad_set.add((night, int(p)))

print(f"Bad (night, petal) pairs: {len(bad_set)}")

# tile → lastnight for dark tiles
tiles = pd.read_csv(TILES, usecols=["TILEID", "PROGRAM", "LASTNIGHT"])
dark_tiles = tiles[tiles["PROGRAM"] == "dark"][["TILEID", "LASTNIGHT"]]

print("Reading zcatalog (dark only)...")
data = fitsio.read(ZCAT, ext="ZCATALOG",
                   columns=["TARGETID", "TILEID", "PROGRAM", "PETAL_LOC"])
df = pd.DataFrame({
    "TARGETID": data["TARGETID"].byteswap().view(data["TARGETID"].dtype.newbyteorder()),
    "TILEID":   data["TILEID"].byteswap().view(data["TILEID"].dtype.newbyteorder()),
    "PROGRAM":  [p.strip() for p in data["PROGRAM"]],
    "PETAL":    data["PETAL_LOC"].byteswap().view(data["PETAL_LOC"].dtype.newbyteorder()),
})
df = df[df["PROGRAM"] == "dark"].copy()
df = df.merge(dark_tiles, on="TILEID", how="left")
print(f"  {len(df):,} dark targets")

df["is_bad"] = [
    (int(night), int(petal)) in bad_set
    for night, petal in zip(df["LASTNIGHT"], df["PETAL"])
]

print("Reading outliers...")
outliers = pd.read_csv(OUTLIERS, usecols=["TARGETID", "TILEID"])
outlier_keys = set(zip(outliers["TARGETID"], outliers["TILEID"]))
df["is_outlier"] = [
    (t, tid) in outlier_keys
    for t, tid in zip(df["TARGETID"], df["TILEID"])
]

# --- per-petal comparison ---
petals = range(10)
frac_bad  = []
err_bad   = []
frac_good = []
err_good  = []

for petal in petals:
    sp = df[df["PETAL"] == petal]
    for is_bad, frac_list, err_list in [(True, frac_bad, err_bad), (False, frac_good, err_good)]:
        sub = sp[sp["is_bad"] == is_bad]
        n_tot = len(sub)
        n_out = sub["is_outlier"].sum()
        frac_list.append(n_out / n_tot if n_tot > 0 else np.nan)
        err_list.append(np.sqrt(n_out) / n_tot if n_tot > 0 else np.nan)

fig, axes = plt.subplots(2, 1, figsize=(10, 9))

# panel 1: per-petal bad vs good
ax = axes[0]
x = np.arange(len(petals))
w = 0.35
ax.bar(x - w/2, frac_bad,  w, yerr=err_bad,  capsize=4, label="bad night", alpha=0.8)
ax.bar(x + w/2, frac_good, w, yerr=err_good, capsize=4, label="good night", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels([f"Petal {p}" for p in petals], rotation=45)
ax.set_ylabel("Outlier fraction")
ax.set_title("Loa dark — outlier fraction: bad vs good nights per petal")
ax.legend()

# panel 2: overall bad vs good
ax = axes[1]
results = {}
for label, flag in [("bad night", True), ("good night", False)]:
    sub = df[df["is_bad"] == flag]
    n_tot = len(sub)
    n_out = sub["is_outlier"].sum()
    frac  = n_out / n_tot
    err   = np.sqrt(n_out) / n_tot
    results[label] = (frac, err, n_tot)
    print(f"{label}: fraction={frac:.4f} ± {err:.4f}  (N={n_tot:,})")

labels = list(results.keys())
fracs  = [results[l][0] for l in labels]
errs   = [results[l][1] for l in labels]
ax.bar(labels, fracs, yerr=errs, capsize=6, alpha=0.8)
ax.set_ylabel("Outlier fraction")
ax.set_title("Loa dark — overall outlier fraction: bad vs good nights")

fig.tight_layout()
outpath = "plots/bad_petal_vs_outliers_dark_loa.png"
fig.savefig(outpath, dpi=150)
plt.close(fig)
print(f"Saved {outpath}")
