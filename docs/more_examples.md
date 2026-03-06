# More Examples

## L2 Swath Data

L2 data uses 2-D lat/lon arrays.  Use `geometry="swath"` and install the `swath` extras:

```bash
pip install point-collocation[earthaccess,swath]
```

### Plan and matchup

```python
import earthaccess
import point_collocation as pc
import pandas as pd

earthaccess.login()

df_points = pd.DataFrame({
    "lat":  [34.5,  35.1 ],
    "lon":  [-120.3, -119.8],
    "time": pd.to_datetime(["2023-06-01", "2023-06-01"]),
})

p = pc.plan(
    df_points,
    source_kwargs={"short_name": "PACE_OCI_L2_AOP_NRT"},
    time_buffer="3h",      # ±3 h buffer to catch orbit overpasses
)
p.summary()

# Inspect variables in a swath granule
p.show_variables(geometry="swath")

# Run the matchup (xoak nearest-neighbour on 2-D grids)
out = pc.matchup(
    p,
    geometry="swath",
    variables=["Rrs"],
)
print(out)
```

### Open a swath granule manually

```python
ds = p.open_dataset(p[0], geometry="swath")
print(ds)
```

---

## Multi-File / Multi-Day

`plan.open_mfdataset()` concatenates several granules into one dataset:

```python
# Subset the plan to the first 3 granules and open them together
ds_all = p.open_mfdataset(p[0:3], geometry="grid")
print(ds_all)   # adds a "granule" dimension
```

---

## Time Buffer

Use `time_buffer` when field measurements are not exactly synchronised with
the satellite overpass:

```python
p = pc.plan(
    df_points,
    source_kwargs={"short_name": "PACE_OCI_L3M_RRS"},
    time_buffer="12h",   # match granules within ±12 hours
)
p.summary()
```

---

## Subset a Large Plan

Run a quick test on the first few points before committing to the full matchup:

```python
# Test on the first 5 points only
out_test = pc.matchup(p[0:5], geometry="grid", variables=["Rrs"])
print(out_test)
```

---

## xarray Accessor

Register the optional `Dataset.pc` accessor for interactive exploration:

```python
import xarray as xr
import point_collocation.extensions.accessor  # noqa: F401

ds = xr.open_dataset("my_granule.nc")
out = ds.pc.extract_points(df_points, variables=["sst"])
```
