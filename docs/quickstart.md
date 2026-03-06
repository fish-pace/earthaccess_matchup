# Quickstart

This guide shows a complete end-to-end workflow for **gridded (L3) data**.
For L2 swath data see [More Examples](more_examples.md).

## 1. Log in to NASA Earthdata

```python
import earthaccess
earthaccess.login()          # prompts for credentials on first run;
                             # caches them in ~/.netrc automatically
```

## 2. Define your field points

Create a `pandas.DataFrame` with at least `lat`, `lon`, and `time` columns:

```python
import pandas as pd

df_points = pd.DataFrame({
    "lat":  [34.5,       35.1,       33.8      ],
    "lon":  [-120.3,     -119.8,     -121.0    ],
    "time": pd.to_datetime(["2023-06-01", "2023-06-02", "2023-06-01"]),
})
```

You can use a `date` column instead of `time`; this is handled automatically — the time-of-day is set to noon (12:00 UTC) so that date-only inputs match the correct granule.

## 3. Build a plan

`pc.plan()` searches NASA Earthdata for granules that cover your points and
returns a `Plan` object — no data is downloaded yet.

```python
import point_collocation as pc

p = pc.plan(
    df_points,
    source_kwargs={
        "short_name": "PACE_OCI_L3M_RRS",   # NASA EarthData collection short name
        "granule_name": "*.DAY.*.4km.*",    # optional glob filter
    },
)
p.summary()
```

Example output:

```
Plan: 3 points → 2 unique granule(s)
  Points with 0 matches : 0
  Points with >1 matches: 0
  Time buffer: 0 days 00:00:00

First 3 point(s):
  [0] lat=34.5000, lon=-120.3000, time=2023-06-01 00:00:00: 1 match(es)
  [1] lat=35.1000, lon=-119.8000, time=2023-06-02 00:00:00: 1 match(es)
  [2] lat=33.8000, lon=-121.0000, time=2023-06-01 00:00:00: 1 match(es)
```

## 4. Inspect available variables

Before running the full matchup, see which variables are in the granules:

```python
p.show_variables(geometry="grid")
```

Example output:

```
geometry     : 'grid'
open_method  : 'dataset'
Dimensions : {'lat': 4320, 'lon': 8640, 'wavelength': 184}
Variables  : ['Rrs', 'aot_865', 'angstrom', ...]

Geolocation: ('lon', 'lat') — lon dims=('lon',), lat dims=('lat',)
```

## 5. Run the matchup

```python
out = pc.matchup(p, geometry="grid", variables=["Rrs_443", "Rrs_555"])
print(out)
```

`matchup()` returns a `pandas.DataFrame` with one row per (point × granule) pair:

| lat | lon | time | granule_id | Rrs_443 | Rrs_555 |
|-----|-----|------|------------|---------|---------|
| 34.5 | -120.3 | 2023-06-01 | … | 0.0032 | 0.0021 |
| 35.1 | -119.8 | 2023-06-02 | … | 0.0028 | 0.0019 |
| 33.8 | -121.0 | 2023-06-01 | … | 0.0035 | 0.0024 |

Points with no matching granule contribute a single row of `NaN` values.

## 6. Open a single granule interactively

```python
ds = p.open_dataset(p[0])
print(ds)
```

This is useful for exploring the dataset structure before a full matchup run.

## Tips

- Use `time_buffer="12h"` to match points to granules that cover a ±12-hour window.
- Pass `open_dataset_kwargs={"engine": "netcdf4"}` to override the default HDF5 engine.
- See [API Reference](api.md) for all parameters.
