import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

loa = pd.read_csv('/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv')
mat = pd.read_csv('/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv')

tiles_loa = pd.read_csv('/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv', usecols=['TILEID','PROGRAM'])
tiles_mat = pd.read_csv('/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv', usecols=['TILEID','PROGRAM'])

loa = loa.merge(tiles_loa, on='TILEID', how='left')
mat = mat.merge(tiles_mat, on='TILEID', how='left')

PROGRAMS = ['dark', 'bright', 'backup']
results = {}
for program in PROGRAMS:
    sl = loa[loa['PROGRAM'] == program]
    sm = mat[mat['PROGRAM'] == program]
    keys_l = set(zip(sl['TARGETID'], sl['FIBER'], sl['TILEID']))
    keys_m = set(zip(sm['TARGETID'], sm['FIBER'], sm['TILEID']))
    results[program] = {
        'Loa only':   len(keys_l - keys_m),
        'Common':     len(keys_l & keys_m),
        'Matterhorn only': len(keys_m - keys_l),
    }
    print(f"{program}: {results[program]}")

categories = ['Loa only', 'Common', 'Matterhorn only']
colors     = ['C0', 'C2', 'C1']
x = np.arange(len(PROGRAMS))
width = 0.25

fig, ax = plt.subplots(figsize=(10, 6))
for i, (cat, color) in enumerate(zip(categories, colors)):
    vals = [results[p][cat] for p in PROGRAMS]
    ax.bar(x + (i - 1) * width, vals, width, label=cat, color=color)

ax.set_xticks(x)
ax.set_xticklabels(PROGRAMS)
ax.set_ylabel('Number of outlier triads (TARGETID, FIBER, TILEID)')
ax.set_title('Loa vs Matterhorn outlier overlap by program')
ax.legend()
fig.tight_layout()
fig.savefig('plots/outlier_overlap_loa_matterhorn.png', dpi=150)
print('Saved plots/outlier_overlap_loa_matterhorn.png')
