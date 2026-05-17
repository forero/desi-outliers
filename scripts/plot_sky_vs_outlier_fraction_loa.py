"""
Correlate SKY_MAG_AB_GFA_MEAN with outlier fraction per tile (Loa, main survey).
Three panels: dark, bright, backup.
"""
import fitsio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

OUTLIERS  = '/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv'
ZCATALOG  = '/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits'
CONDITIONS = 'data/tile_conditions_loa.csv'

# --- load outlier counts per tile -------------------------------------------
print("Loading outlier catalog ...")
out = pd.read_csv(OUTLIERS, usecols=['TARGETID', 'TILEID'])
n_out = out.groupby('TILEID').size().rename('N_OUTLIERS')

# --- load zcatalog (only TILEID, SURVEY, PROGRAM) for total counts ----------
print("Loading zcatalog (TILEID, SURVEY, PROGRAM only) ...")
zdata = fitsio.read(ZCATALOG, ext=1, columns=['TILEID', 'SURVEY', 'PROGRAM'])
zdf = pd.DataFrame({
    'TILEID':  zdata['TILEID'].byteswap().newbyteorder(),
    'SURVEY':  zdata['SURVEY'].astype('U8'),
    'PROGRAM': zdata['PROGRAM'].astype('U8'),
})
del zdata

# filter to main survey
zdf = zdf[zdf['SURVEY'] == 'main']
n_tot = zdf.groupby('TILEID').size().rename('N_TOTAL')
prog  = zdf.groupby('TILEID')['PROGRAM'].agg(lambda x: x.mode().iloc[0])

# --- merge ------------------------------------------------------------------
cond = pd.read_csv(CONDITIONS)
cond = cond[cond['SURVEY'] == 'main']

tile = (pd.DataFrame({'N_TOTAL': n_tot, 'PROGRAM': prog})
          .reset_index()
          .merge(n_out.reset_index(), on='TILEID', how='left'))
tile['N_OUTLIERS'] = tile['N_OUTLIERS'].fillna(0).astype(int)
tile['FRAC'] = tile['N_OUTLIERS'] / tile['N_TOTAL']

tile = tile.merge(cond[['TILEID', 'SKY_MAG_AB_GFA_MEAN']], on='TILEID', how='inner')
tile = tile.dropna(subset=['SKY_MAG_AB_GFA_MEAN', 'FRAC'])

print(f"Tiles after merge: {len(tile)}")
print(tile.groupby('PROGRAM')[['N_TOTAL', 'N_OUTLIERS']].sum())

# --- plot -------------------------------------------------------------------
programs   = ['dark', 'bright', 'backup']
colors     = ['#1f77b4', '#ff7f0e', '#2ca02c']
xlabels    = ['Faint (dark sky)', 'Bright (moon)']

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)

for ax, prog_name, color in zip(axes, programs, colors):
    sub = tile[tile['PROGRAM'] == prog_name].copy()
    if len(sub) < 10:
        ax.set_title(f'{prog_name.capitalize()} (n={len(sub)})')
        continue

    x = sub['SKY_MAG_AB_GFA_MEAN'].values
    y = sub['FRAC'].values * 100  # percent

    ax.scatter(x, y, s=6, alpha=0.4, color=color, rasterized=True)

    # running median in bins
    bins = np.percentile(x, np.linspace(0, 100, 21))
    bins = np.unique(bins)
    bx, bmed, blo, bhi = [], [], [], []
    for i in range(len(bins) - 1):
        mask = (x >= bins[i]) & (x < bins[i+1])
        if mask.sum() < 5:
            continue
        yb = y[mask]
        bx.append(0.5 * (bins[i] + bins[i+1]))
        bmed.append(np.median(yb))
        blo.append(np.percentile(yb, 16))
        bhi.append(np.percentile(yb, 84))
    bx   = np.array(bx)
    bmed = np.array(bmed)
    ax.plot(bx, bmed, 'k-', lw=2, label='Median')
    ax.fill_between(bx, blo, bhi, alpha=0.2, color='k', label='16–84th pct')

    r, p = stats.pearsonr(x, y)
    slope, intercept, *_ = stats.linregress(x, y)
    xfit = np.linspace(x.min(), x.max(), 100)
    ax.plot(xfit, slope * xfit + intercept, 'r--', lw=1.5,
            label=f'r={r:.3f}')

    ax.set_xlabel('Sky brightness (AB mag arcsec⁻²)', fontsize=11)
    ax.set_ylabel('Outlier fraction (%)', fontsize=11)
    ax.set_title(f'{prog_name.capitalize()}  (n={len(sub):,} tiles)', fontsize=12)
    ax.legend(fontsize=9)
    ax.invert_xaxis()   # brighter sky on the right

fig.suptitle('Loa main survey: sky brightness vs UMAP outlier fraction per tile',
             fontsize=13, y=1.01)
fig.tight_layout()

outpath = 'plots/sky_vs_outlier_fraction_loa.png'
fig.savefig(outpath, dpi=150, bbox_inches='tight')
print(f"Saved {outpath}")
