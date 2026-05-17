"""
Compute per-tile average observing conditions from exposures-loa.fits.
Output: data/tile_conditions_loa.csv
"""
import fitsio
import numpy as np
import pandas as pd

EXPOSURES = '/global/cfs/cdirs/desi/spectro/redux/loa/exposures-loa.fits'

COND_COLS = [
    'AIRMASS', 'SEEING_ETC', 'SEEING_GFA',
    'TRANSPARENCY_GFA',
    'SKY_MAG_AB_GFA', 'SKY_MAG_G_SPEC', 'SKY_MAG_R_SPEC', 'SKY_MAG_Z_SPEC',
    'EBV',
]

META_COLS = ['SURVEY', 'PROGRAM', 'FAPRGRM']

print("Reading exposures-loa.fits ...")
data = fitsio.read(EXPOSURES, ext='EXPOSURES',
                   columns=['TILEID', 'EXPTIME'] + META_COLS + COND_COLS)
# Convert big-endian fitsio arrays to native byte order
data_native = {}
for name in data.dtype.names:
    arr = data[name]
    if arr.dtype.byteorder not in ('=', '|', 'native'):
        arr = arr.byteswap().newbyteorder()
    data_native[name] = arr
df = pd.DataFrame(data_native)

# Decode byte strings
for col in df.select_dtypes([object]).columns:
    try:
        df[col] = df[col].str.decode('utf-8').str.strip()
    except AttributeError:
        pass

# Replace sentinel / bad values with NaN
for col in COND_COLS:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df.loc[df[col] <= 0, col] = np.nan   # 0 or negative = missing

agg = {}

# Metadata: take the mode (most common value) per tile
for col in META_COLS:
    agg[col] = df.groupby('TILEID')[col].agg(lambda x: x.mode().iloc[0])

# Count exposures and total exptime
agg['NEXP'] = df.groupby('TILEID')['EXPTIME'].count()
agg['EXPTIME_TOTAL'] = df.groupby('TILEID')['EXPTIME'].sum()

# Mean of condition columns (ignoring NaN)
for col in COND_COLS:
    agg[f'{col}_MEAN'] = df.groupby('TILEID')[col].mean()

out = pd.DataFrame(agg).reset_index()
out = out.sort_values('TILEID').reset_index(drop=True)

outpath = 'data/tile_conditions_loa.csv'
out.to_csv(outpath, index=False, float_format='%.6f')
print(f"Wrote {len(out)} tiles to {outpath}")
print(out.head())
