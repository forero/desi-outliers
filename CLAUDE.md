# desi-outliers

Repo for making plots of DESI spectroscopic outliers identified via UMAP analysis.

## Outlier catalogs

| Production | Path | Rows |
|------------|------|------|
| Matterhorn | `/pscratch/sd/v/vtorresg/umap_analysis/data/matterhorn/sum/all_outliers.csv` | ~2.2M |
| Loa | `/pscratch/sd/v/vtorresg/desi-lenses/df_outliers.csv` | ~1.1M |

Both files share the same schema: `TARGETID, TILEID, FIBER`.

## SPECPROD tile summaries

| Production | Tiles CSV | Tiles FITS |
|------------|-----------|------------|
| Loa | `/global/cfs/cdirs/desi/spectro/redux/loa/tiles-loa.csv` | `…/tiles-loa.fits` |
| Daily (Matterhorn) | `/global/cfs/cdirs/desi/spectro/redux/daily/tiles-daily.csv` | `…/tiles-daily.fits` |

Key columns: `TILEID`, `LASTNIGHT` (used as the thrudate in file paths).

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
└── plots/       # output figures
```

## Zcatalog (Loa)

Per-spectrum redshift catalog with TSNR2 metrics:

```
/global/cfs/cdirs/desi/spectro/redux/loa/zcatalog/v1/zall-tilecumulative-loa.fits
```

Key columns: `TARGETID`, `TILEID`, `PROGRAM`, `TSNR2_LRG` (dark), `TSNR2_BGS` (bright).

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

## Scripts

- `scripts/plot_outliers_by_program.py` — bar chart of outlier counts by program, per production + comparison
- `scripts/plot_outliers_by_fiber.py` — scatter of outliers vs fiber ID, split by program
- `scripts/plot_outliers_per_tile.py` — histogram of outliers per tile, per production + comparison
- `scripts/plot_outliers_per_petal.py` — bar chart of outliers per petal ID, per production + comparison
- `scripts/plot_tsnr_vs_outliers_loa.py` — TSNR distribution and outlier fraction vs TSNR (Loa); usage: `python script.py [dark|bright|backup]`

## Notebooks

- `notebooks/desi-tiles-dr2.ipynb` — tile-level exploration
- `notebooks/check_targetid.ipynb` — per-target spectrum lookup
