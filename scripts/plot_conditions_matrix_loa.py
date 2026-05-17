"""
Summary matrix: Spearman r between per-tile outlier fraction and
observing conditions, Loa main survey.
Red = significant after Bonferroni correction.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

df = pd.read_csv('data/conditions_correlations_loa.csv')

programs = ['dark', 'bright', 'backup']

N_TESTS = len(df)
BONFERRONI = 0.05 / N_TESTS

# Pivot to (condition x program) matrices
r_mat  = df.pivot(index='condition', columns='program', values='spearman_r')[programs]
p_mat  = df.pivot(index='condition', columns='program', values='spearman_p')[programs]

# Order rows by max |r| across programs (descending)
row_order = r_mat.abs().max(axis=1).sort_values(ascending=False).index
r_mat = r_mat.loc[row_order, programs]
p_mat = p_mat.loc[row_order, programs]

# Clean up row labels
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

nrows, ncols = r_mat.shape
fig, ax = plt.subplots(figsize=(6, 7))
ax.set_xlim(-0.5, ncols - 0.5)
ax.set_ylim(-0.5, nrows - 0.5)
ax.set_aspect('equal')

# Colormap for significant cells: white→red scaled by |r|
sig_cmap = plt.cm.Reds

for i, cond in enumerate(row_order):
    for j, prog in enumerate(programs):
        r = r_mat.loc[cond, prog]
        p = p_mat.loc[cond, prog]
        significant = (p < BONFERRONI) and (abs(r) >= 0.05)

        if significant:
            intensity = min(abs(r) / 0.65, 1.0)   # scale: 0.65 maps to full red
            fc = sig_cmap(0.2 + 0.8 * intensity)
            txt_color = 'white' if intensity > 0.5 else 'black'
        else:
            fc = '#e8e8e8'
            txt_color = '#aaaaaa'

        rect = plt.Rectangle((j - 0.5, (nrows - 1 - i) - 0.5), 1, 1,
                              fc=fc, ec='white', lw=1.5)
        ax.add_patch(rect)

        sign = '+' if r >= 0 else '−'
        ax.text(j, nrows - 1 - i, f'{sign}{abs(r):.2f}',
                ha='center', va='center', fontsize=10,
                fontweight='bold' if significant else 'normal',
                color=txt_color)

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
    f'Loa main survey  |  red = significant (Bonferroni p < {BONFERRONI:.4f})',
    fontsize=10, pad=18
)

fig.tight_layout()
outpath = 'plots/conditions_matrix_loa.png'
fig.savefig(outpath, dpi=150, bbox_inches='tight')
print(f"Saved {outpath}")
