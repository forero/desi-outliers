"""
Pearson and Spearman correlations between per-tile outlier fraction
and all observing condition columns, for Loa main survey.
Outputs: data/conditions_correlations_loa.csv + plots/conditions_correlations_loa.png
"""
import fitsio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

OUTLIERS   = '/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv'
ZCATALOG   = '/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits'
CONDITIONS = 'data/tile_conditions_loa.csv'

COND_COLS = [
    'NEXP', 'EXPTIME_TOTAL',
    'AIRMASS_MEAN', 'SEEING_ETC_MEAN', 'SEEING_GFA_MEAN',
    'TRANSPARENCY_GFA_MEAN',
    'SKY_MAG_AB_GFA_MEAN', 'SKY_MAG_G_SPEC_MEAN',
    'SKY_MAG_R_SPEC_MEAN', 'SKY_MAG_Z_SPEC_MEAN',
    'EBV_MEAN',
]

# --- outlier counts per tile ------------------------------------------------
print("Loading outlier catalog ...")
out = pd.read_csv(OUTLIERS, usecols=['TARGETID', 'TILEID'])
n_out = out.groupby('TILEID').size().rename('N_OUTLIERS')

# --- zcatalog: total counts per tile (main survey only) ---------------------
print("Loading zcatalog ...")
zdata = fitsio.read(ZCATALOG, ext=1, columns=['TILEID', 'SURVEY', 'PROGRAM'])
zdf = pd.DataFrame({
    'TILEID':  zdata['TILEID'].byteswap().newbyteorder(),
    'SURVEY':  zdata['SURVEY'].astype('U8'),
    'PROGRAM': zdata['PROGRAM'].astype('U8'),
})
del zdata
zdf = zdf[zdf['SURVEY'] == 'main']
n_tot = zdf.groupby('TILEID').size().rename('N_TOTAL')
prog  = zdf.groupby('TILEID')['PROGRAM'].agg(lambda x: x.mode().iloc[0])

# --- merge conditions -------------------------------------------------------
cond = pd.read_csv(CONDITIONS)
cond = cond[cond['SURVEY'] == 'main']

tile = (pd.DataFrame({'N_TOTAL': n_tot, 'PROGRAM': prog})
          .reset_index()
          .merge(n_out.reset_index(), on='TILEID', how='left'))
tile['N_OUTLIERS'] = tile['N_OUTLIERS'].fillna(0).astype(int)
tile['FRAC'] = tile['N_OUTLIERS'] / tile['N_TOTAL']
tile = tile.merge(cond[['TILEID'] + COND_COLS], on='TILEID', how='inner')

# --- compute correlations ---------------------------------------------------
programs = ['dark', 'bright', 'backup']
rows = []
for prog_name in programs:
    sub = tile[tile['PROGRAM'] == prog_name].dropna(subset=['FRAC'])
    y = sub['FRAC'].values
    for col in COND_COLS:
        x = sub[col].values
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 30:
            continue
        xm, ym = x[mask], y[mask]
        r_p, p_p = stats.pearsonr(xm, ym)
        r_s, p_s = stats.spearmanr(xm, ym)
        rows.append(dict(
            program=prog_name, condition=col, n=mask.sum(),
            pearson_r=r_p, pearson_p=p_p,
            spearman_r=r_s, spearman_p=p_s,
        ))

df_corr = pd.DataFrame(rows)
df_corr = df_corr.sort_values('pearson_r', key=abs, ascending=False)

outcsv = 'data/conditions_correlations_loa.csv'
df_corr.to_csv(outcsv, index=False, float_format='%.4f')
print(f"\nSaved {outcsv}")
print(df_corr.to_string(index=False))

# --- heatmap ----------------------------------------------------------------
pivot_p = df_corr.pivot(index='condition', columns='program', values='pearson_r')
pivot_s = df_corr.pivot(index='condition', columns='program', values='spearman_r')

# order rows by max abs Pearson across programs
order = pivot_p.abs().max(axis=1).sort_values(ascending=False).index
pivot_p = pivot_p.loc[order, programs]
pivot_s = pivot_s.loc[order, programs]

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
for ax, pivot, title in zip(axes, [pivot_p, pivot_s], ['Pearson r', 'Spearman r']):
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdBu_r', vmin=-0.5, vmax=0.5)
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks(range(len(programs)))
    ax.set_xticklabels([p.capitalize() for p in programs], fontsize=11)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.set_title(title, fontsize=12)
    for i in range(len(order)):
        for j in range(len(programs)):
            val = pivot.values[i, j]
            if np.isfinite(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=8, color='white' if abs(val) > 0.3 else 'black')

fig.suptitle('Loa main survey: correlation of observing conditions with outlier fraction',
             fontsize=12, y=1.01)
fig.tight_layout()
outpng = 'plots/conditions_correlations_loa.png'
fig.savefig(outpng, dpi=150, bbox_inches='tight')
print(f"Saved {outpng}")
