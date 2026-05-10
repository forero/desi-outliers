# desi-outliers

Repo for making plots of DESI spectroscopic outliers identified via UMAP analysis.

## Outlier catalogs

| Production | Path | Rows |
|------------|------|------|
| Matterhorn | `/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv` | ~2.2M |
| Loa | `/pscratch/sd/v/vtorresg/umap_analysis/data/loa/sum/all_outliers.csv` | ~1.1M |

Both files share the same schema: `TARGETID, TILEID, FIBER`.

## SPECPROD tile summaries

| Production | Tiles CSV | Tiles FITS |
|------------|-----------|------------|
| Loa | `/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv` | `…/tiles-loa.fits` |
| Matterhorn | `/global/cfs/cdirs/desi/spectro/redux/matterhorn/tiles-matterhorn.csv` | `…/tiles-matterhorn.fits` |

Key columns: `TILEID`, `LASTNIGHT` (used as the thrudate in file paths), `PROGRAM`, `SURVEY` (`main`, `sv3`, `cmx`, etc.).

## Tile file layout

Coadded spectra for a given tile live at:

```
/global/cfs/cdirs/desi/spectro/redux/{SPECPROD}/tiles/cumulative/{TILEID}/{LASTNIGHT}/
```

Files inside are split by petal (0–9):

- `coadd-{petal}-{tileid}-thru{lastnight}.fits`
- `spectra-{petal}-{tileid}-thru{lastnight}.fits.gz`
- `redrock-{petal}-{tileid}-thru{lastnight}.fits`

The petal for a given fiber is `petal = fiber // 500`.

## Repo structure

```
desi-outliers/
├── notebooks/   # exploratory Jupyter notebooks
├── scripts/     # production Python scripts
├── plots/       # output figures
└── html/        # HTML reports and tables
```

## Zcatalog (Loa)

Per-spectrum redshift catalog with TSNR2 metrics:

```
/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits
```

Key columns: `TARGETID`, `TILEID`, `SURVEY`, `PROGRAM`, `ZWARN`, `TSNR2_LRG` (dark), `TSNR2_BGS` (bright).

## Selected tiles for visual inspection (Loa)

Tiles chosen at median, median−1σ, and median+1σ of outlier fraction per tile.

**Dark** (median=0.48%, std=0.52%):

| Level | TILEID | N outliers |
|-------|--------|-----------|
| median − 1σ | 2362 | 2 |
| median | 10981 | 24 |
| median + 1σ | 6190 | 50 |

**Bright** (median=2.04%, std=0.89%):

| Level | TILEID | N outliers |
|-------|--------|-----------|
| median − 1σ | 12 | 57 |
| median | 21542 | 102 |
| median + 1σ | 20353 | 132 |

Total outliers across these 6 tiles: 367.

## External QA files (Loa)

| File | Description |
|------|-------------|
| `/global/cfs/cdirs/desicollab/users/rongpu/redshift_qa/new/kibo/per_fiber_qa_stats.fits` | Per-fiber QA stats (5000 rows); key cols: `FIBER`, `lrg_frac_fail`, `bgs_bright_frac_fail`. Sentinel value −99 = missing. |
| `/global/cfs/cdirs/desi/survey/catalogs/DA2/LSS/loa-v1/bad_nz_fibers_ks_test.txt` | 12 fibers flagged as bad by KS n(z) test: 1067,1261,1329,2183,2246,2587,2669,3358,3500,3546,3974,4461 |

**Key finding**: UMAP high-outlier fibers (>mean+3σ per petal) and KS bad fibers are almost completely disjoint — they detect different failure modes. Only fiber 3974 appears in both (BGS).

## VI data (Loa)

Visual inspection of 6 randomly selected main-survey tiles (3 dark, 3 bright); results in `data/vi_tiles_loa.csv`.

**VI fractions (95% Clopper-Pearson)**:

| Program | N inspected | VI problems | No VI problem | ZWARN≠0 |
|---------|------------|-------------|---------------|---------|
| Dark | 79 | 79.7% [69.2%, 88.0%] | 16 | 16.5% [9.1%, 26.5%] |
| Bright | 312 | 63.5% [57.9%, 68.8%] | 114 | 1.0% [0.2%, 2.8%] |
| All | 391 | 66.8% [61.8%, 71.4%] | 130 | 4.1% [2.4%, 6.6%] |

**Extrapolated no-VI-problem outliers in full Loa main survey**:

| Program | N total | Estimated no-VI-problem |
|---------|---------|------------------------|
| Dark | 191,411 | 38,767 [23,051 – 58,946] |
| Bright | 463,543 | 169,371 [144,558 – 195,382] |
| Combined | 654,954 | 217,760 [187,271 – 249,924] |

**ZWARN≠0 in full Loa main survey** (from zcatalog cross-match):

| Program | N outliers | ZWARN≠0 | Fraction |
|---------|-----------|---------|---------|
| Dark | 191,411 | 30,692 | 16.03% [15.87%, 16.20%] |
| Bright | 463,543 | 8,221 | 1.77% [1.74%, 1.81%] |
| Backup | 349,927 | 419 | 0.12% [0.11%, 0.13%] |
| Dark+Bright | 654,954 | 38,913 | 5.94% [5.88%, 6.00%] |
| All | 1,004,881 | 39,332 | 3.91% [3.88%, 3.95%] |

## HTML outputs

All HTML files are saved to `html/` and automatically copied to `/global/cfs/cdirs/desi/users/forero/outliers/`.

- `html/dark_common_outliers_loa_matterhorn.html` — 6,188 dark tiles with common outliers in Loa+Matterhorn, sorted by count, with inspector links
- `html/high_outlier_fibers_loa_matterhorn.html` — fibers with raw outlier count >mean+3σ per petal (LRG/BGS × Loa/Matterhorn), plus cross-comparisons across tracers and specprods; 7 fibers common to all four: 357, 464, 466, 651, 2171, 2773, 4923
- `html/mean_tiles_loa_matterhorn.html` — 3 randomly selected main-survey tiles per program (dark/bright) for Loa and for Matterhorn tiles not in Loa, with inspector links

## Scripts

- `scripts/plot_outliers_by_program.py` — bar chart of outlier counts by program, per production + comparison
- `scripts/plot_outliers_by_fiber.py` — scatter of outliers vs fiber ID, split by program (dark/bright/backup panels)
- `scripts/plot_outliers_per_tile.py` — histogram of outliers per tile, per production + normalized comparison
- `scripts/plot_outliers_per_petal.py` — bar chart of outliers per petal ID, per production + comparison
- `scripts/plot_tsnr_vs_outliers_loa.py` — TSNR distribution and outlier fraction vs TSNR (Loa); usage: `python script.py [dark|bright|backup]`
- `scripts/plot_outliers_by_radius_loa.py` — outlier fraction vs focal plane radius, 3 programs (Loa)
- `scripts/plot_outliers_by_radius_per_petal_loa.py` — outlier fraction vs radius per petal, 2×5 panels (Loa)
- `scripts/plot_outlier_fraction_vs_qa_per_fiber_loa.py` — outlier count and QA failure rate vs fiber ID + scatter with correlation (LRG, BGS)
- `scripts/plot_qa_correlation_per_petal_loa.py` — scatter of outlier fraction vs QA failure rate per petal, 2×5 panels (LRG, BGS)
- `scripts/plot_outlier_overlap_loa_matterhorn.py` — Loa-only / common / Matterhorn-only outlier counts by program
- `scripts/plot_bad_petal_vs_outliers_loa.py` — outlier fraction for bad vs good (night, petal) pairs in dark program (Loa)
- `scripts/plot_outliers_per_month_matterhorn.py` — outlier counts per month by program (Matterhorn)
- `scripts/plot_outliers_heatmap_month_petal_matterhorn.py` — heatmap of outlier fraction per month × petal (Matterhorn); denominator = n_tiles × 500
- `scripts/make_dark_common_outliers_html.py` — generates `dark_common_outliers_loa_matterhorn.html`
- `scripts/make_high_outlier_fibers_html.py` — generates `high_outlier_fibers_loa_matterhorn.html`
- `scripts/make_mean_tiles_html.py` — generates `mean_tiles_loa_matterhorn.html`; 3 randomly sampled main-survey tiles per program for Loa and Matterhorn-only tiles (seed=42)
- `scripts/vi_statistics_loa.py` — Clopper-Pearson VI fractions (bad/good/zwarn) per tile and aggregated by program, from `data/vi_tiles_loa.csv`
- `scripts/zwarn_fraction_loa.py` — ZWARN≠0 fraction in full Loa main-survey outlier catalog, cross-matched against zcatalog; results by program with Clopper-Pearson intervals

## Notebooks

- `notebooks/desi-tiles-dr2.ipynb` — tile-level exploration
- `notebooks/check_targetid.ipynb` — per-target spectrum lookup
