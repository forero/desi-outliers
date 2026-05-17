"""
Same as plot_conditions_matrix_loa.py but with ±1σ error bars from
splitting tiles into 10 random groups and computing Spearman r per group.
Significance: |r_mean| / r_std > 2  (i.e. mean differs from 0 by >2σ across groups).
"""
import fitsio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

OUTLIERS   = '/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv'
ZCATALOG   = '/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits'
CONDITIONS = 'data/tile_conditions_loa.csv'
N_GROUPS   = 10
RNG        = np.random.default_rng(42)

COND_COLS = [
    'NEXP', 'EXPTIME_TOTAL',
    'AIRMASS_MEAN', 'SEEING_ETC_MEAN', 'SEEING_GFA_MEAN',
    'TRANSPARENCY_GFA_MEAN',
    'SKY_MAG_AB_GFA_MEAN', 'SKY_MAG_G_SPEC_MEAN',
    'SKY_MAG_R_SPEC_MEAN', 'SKY_MAG_Z_SPEC_MEAN',
    'EBV_MEAN',
]

# --- build per-tile dataframe -----------------------------------------------
print("Loading outlier catalog ...")
out = pd.read_csv(OUTLIERS, usecols=['TARGETID', 'TILEID'])
n_out = out.groupby('TILEID').size().rename('N_OUTLIERS')

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

cond = pd.read_csv(CONDITIONS)
cond = cond[cond['SURVEY'] == 'main']

tile = (pd.DataFrame({'N_TOTAL': n_tot, 'PROGRAM': prog})
          .reset_index()
          .merge(n_out.reset_index(), on='TILEID', how='left'))
tile['N_OUTLIERS'] = tile['N_OUTLIERS'].fillna(0).astype(int)
tile['FRAC'] = tile['N_OUTLIERS'] / tile['N_TOTAL']
tile = tile.merge(cond[['TILEID'] + COND_COLS], on='TILEID', how='inner')

# --- bootstrap: split into N_GROUPS, compute Spearman r per group -----------
programs = ['dark', 'bright', 'backup']

results = {}   # (cond, prog) -> array of N_GROUPS r values

for prog_name in programs:
    sub = tile[tile['PROGRAM'] == prog_name].dropna(subset=['FRAC']).copy()
    sub = sub.reset_index(drop=True)
    n = len(sub)
    group_ids = RNG.permutation(n) % N_GROUPS   # assign each tile to a group

    for col in COND_COLS:
        rs = []
        for g in range(N_GROUPS):
            mask = (group_ids == g)
            xg = sub.loc[mask, col].values
            yg = sub.loc[mask, 'FRAC'].values
            valid = np.isfinite(xg) & np.isfinite(yg)
            if valid.sum() < 10:
                rs.append(np.nan)
            else:
                r, _ = stats.spearmanr(xg[valid], yg[valid])
                rs.append(r)
        results[(col, prog_name)] = np.array(rs)

# --- summarise --------------------------------------------------------------
rows = []
for (col, prog_name), rs in results.items():
    valid = rs[np.isfinite(rs)]
    if len(valid) == 0:
        continue
    r_mean = valid.mean()
    r_std  = valid.std(ddof=1)
    rows.append(dict(condition=col, program=prog_name,
                     r_mean=r_mean, r_std=r_std))

df_boot = pd.DataFrame(rows)

# --- pivot ------------------------------------------------------------------
r_mean_mat = df_boot.pivot(index='condition', columns='program', values='r_mean')[programs]
r_std_mat  = df_boot.pivot(index='condition', columns='program', values='r_std')[programs]

row_order = r_mean_mat.abs().max(axis=1).sort_values(ascending=False).index
r_mean_mat = r_mean_mat.loc[row_order, programs]
r_std_mat  = r_std_mat.loc[row_order, programs]

label_map = {
    'NEXP':                   'N exposures',
    'EXPTIME_TOTAL':          'Total exp time',
    'EBV_MEAN':               'E(B-V)',
    'TRANSPARENCY_GFA_MEAN':  'Transparency (GFA)',
    'SEEING_GFA_MEAN':        'Seeing (GFA)',
    'SEEING_ETC_MEAN':        'Seeing (ETC)',
    'SKY_MAG_AB_GFA_MEAN':    'Sky mag AB (GFA)',
    'SKY_MAG_Z_SPEC_MEAN':    'Sky mag z (spec)',
    'SKY_MAG_R_SPEC_MEAN':    'Sky mag r (spec)',
    'SKY_MAG_G_SPEC_MEAN':    'Sky mag g (spec)',
    'AIRMASS_MEAN':           'Airmass',
}
ylabels = [label_map.get(r, r) for r in row_order]

# --- plot -------------------------------------------------------------------
nrows, ncols = r_mean_mat.shape
fig, ax = plt.subplots(figsize=(6, 8))
ax.set_xlim(-0.5, ncols - 0.5)
ax.set_ylim(-0.5, nrows - 0.5)
ax.set_aspect('equal')

sig_cmap = plt.cm.Reds

for i, cond_name in enumerate(row_order):
    for j, prog_name in enumerate(programs):
        r   = r_mean_mat.loc[cond_name, prog_name]
        std = r_std_mat.loc[cond_name, prog_name]

        # significant if mean is >2σ away from zero
        significant = (abs(r) > 2 * std) and (abs(r) >= 0.05)

        if significant:
            intensity = min(abs(r) / 0.65, 1.0)
            fc = sig_cmap(0.2 + 0.8 * intensity)
            r_color   = 'white' if intensity > 0.5 else 'black'
            std_color = 'white' if intensity > 0.5 else '#444444'
        else:
            fc        = '#e8e8e8'
            r_color   = '#aaaaaa'
            std_color = '#bbbbbb'

        rect = plt.Rectangle((j - 0.5, (nrows - 1 - i) - 0.5), 1, 1,
                              fc=fc, ec='white', lw=1.5)
        ax.add_patch(rect)

        sign = '+' if r >= 0 else '−'
        row_y = nrows - 1 - i
        ax.text(j, row_y + 0.15, f'{sign}{abs(r):.2f}',
                ha='center', va='center', fontsize=10,
                fontweight='bold' if significant else 'normal',
                color=r_color)
        ax.text(j, row_y - 0.22, f'±{std:.2f}',
                ha='center', va='center', fontsize=7.5,
                color=std_color)

ax.set_xticks(range(ncols))
ax.set_xticklabels([p.capitalize() for p in programs], fontsize=12)
ax.xaxis.set_ticks_position('top')
ax.xaxis.set_label_position('top')
ax.set_yticks(range(nrows))
ax.set_yticklabels(ylabels[::-1], fontsize=10)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_title(
    f'Spearman r: outlier fraction vs observing conditions\n'
    f'Loa main survey  |  ±1σ from {N_GROUPS}-group split  |  '
    f'red = |r̄| > 2σ and |r̄| ≥ 0.05',
    fontsize=9, pad=18
)

fig.tight_layout()
outpath = 'plots/conditions_matrix_bootstrap_loa.png'
fig.savefig(outpath, dpi=150, bbox_inches='tight')
print(f"Saved {outpath}")
