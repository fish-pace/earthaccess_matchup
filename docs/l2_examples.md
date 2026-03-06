# L2 matchups with PACE data -- RRS

* Create a plan for files to use `pc.plan()`
* Print the plan to check it `print(plan.summary())`
* Do the plan and get matchups `pc.matchup(plan, geometry="swath")`

## Prerequisite -- Login to EarthData

The examples here use NASA EarthData and you need to have an account with EarthData. Make sure you can login.


```python
import earthaccess
import xoak
earthaccess.login()
```




    <earthaccess.auth.Auth at 0x7f66b86c5880>



## Here are the level 2 datasets


```python
import earthaccess
results = earthaccess.search_datasets(instrument="oci")

short_names = [
    item.summary()["short-name"]
    for item in results
    if "L2" in item.summary()["short-name"]
]

print(short_names)
```

    ['PACE_OCI_L2_UVAI_UAA_NRT', 'PACE_OCI_L2_UVAI_UAA', 'PACE_OCI_L2_AER_UAA_NRT', 'PACE_OCI_L2_AER_UAA', 'PACE_OCI_L2_AOP_NRT', 'PACE_OCI_L2_AOP', 'PACE_OCI_L2_CLOUD_MASK_NRT', 'PACE_OCI_L2_CLOUD_MASK', 'PACE_OCI_L2_CLOUD_NRT', 'PACE_OCI_L2_CLOUD', 'PACE_OCI_L2_LANDVI_NRT', 'PACE_OCI_L2_LANDVI', 'PACE_OCI_L2_BGC_NRT', 'PACE_OCI_L2_BGC', 'PACE_OCI_L2_IOP_NRT', 'PACE_OCI_L2_IOP', 'PACE_OCI_L2_PAR_NRT', 'PACE_OCI_L2_PAR', 'PACE_OCI_L2_SFREFL_NRT', 'PACE_OCI_L2_SFREFL', 'PACE_OCI_L2_TRGAS_NRT', 'PACE_OCI_L2_TRGAS']


## Load some points


```python
from pathlib import Path
import earthaccess
import point_collocation as pc
import pandas as pd

HERE = Path.cwd()
POINTS_CSV = HERE / "fixtures" / "points.csv"
df_points = pd.read_csv(POINTS_CSV)  # lat, lon, date columns
print(len(df_points))
df_points.head()
```

    595





<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>lat</th>
      <th>lon</th>
      <th>date</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>27.3835</td>
      <td>-82.7375</td>
      <td>2024-06-13</td>
    </tr>
    <tr>
      <th>1</th>
      <td>27.1190</td>
      <td>-82.7125</td>
      <td>2024-06-14</td>
    </tr>
    <tr>
      <th>2</th>
      <td>26.9435</td>
      <td>-82.8170</td>
      <td>2024-06-14</td>
    </tr>
    <tr>
      <th>3</th>
      <td>26.6875</td>
      <td>-82.8065</td>
      <td>2024-06-14</td>
    </tr>
    <tr>
      <th>4</th>
      <td>26.6675</td>
      <td>-82.6455</td>
      <td>2024-06-14</td>
    </tr>
  </tbody>
</table>
</div>



## Get a plan for matchups from PACE data


```python
%%time
# bounding_box = (lon_min, lat_min, lon_max, lat_max)
import point_collocation as pc
plan = pc.plan(
    df_points[0:100], # -82.7375, 27.3835	
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L2_AOP",
    },
    time_buffer="12h"
)
```

    CPU times: user 336 ms, sys: 19.5 ms, total: 356 ms
    Wall time: 2.03 s



```python
plan.summary()
```

    Plan: 100 points → 24 unique granule(s)
      Points with 0 matches : 0
      Points with >1 matches: 20
      Time buffer: 0 days 12:00:00
    
    First 5 point(s):
      [0] lat=27.3835, lon=-82.7375, time=2024-06-13 12:00:00: 2 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240613T171620.L2.OC_AOP.V3_1.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240613T184939.L2.OC_AOP.V3_1.nc
      [1] lat=27.1190, lon=-82.7125, time=2024-06-14 12:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240614T175104.L2.OC_AOP.V3_1.nc
      [2] lat=26.9435, lon=-82.8170, time=2024-06-14 12:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240614T175104.L2.OC_AOP.V3_1.nc
      [3] lat=26.6875, lon=-82.8065, time=2024-06-14 12:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240614T175104.L2.OC_AOP.V3_1.nc
      [4] lat=26.6675, lon=-82.6455, time=2024-06-14 12:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20240614T175104.L2.OC_AOP.V3_1.nc



```python
plan.show_variables(geometry="swath")
```

    geometry     : 'swath'
    open_method  : 'datatree-merge'
    Dimensions : {'number_of_bands': 286, 'number_of_reflective_bands': 286, 'wavelength_3d': 172, 'number_of_lines': 1710, 'pixels_per_line': 1272}
    Variables  : ['wavelength', 'vcal_gain', 'vcal_offset', 'F0', 'aw', 'bbw', 'k_oz', 'k_no2', 'Tau_r', 'year', 'day', 'msec', 'time', 'detnum', 'mside', 'slon', 'clon', 'elon', 'slat', 'clat', 'elat', 'csol_z', 'Rrs', 'Rrs_unc', 'aot_865', 'angstrom', 'avw', 'nflh', 'l2_flags', 'longitude', 'latitude', 'tilt']
    
    Geolocation: ('longitude', 'latitude') — lon dims=('number_of_lines', 'pixels_per_line'), lat dims=('number_of_lines', 'pixels_per_line')
    
    DataTree groups (detail):
      /
        Dimensions : {}
        Variables  : []
      /sensor_band_parameters
        Dimensions : {'number_of_bands': 286, 'number_of_reflective_bands': 286, 'wavelength_3d': 172}
        Variables  : ['wavelength', 'vcal_gain', 'vcal_offset', 'F0', 'aw', 'bbw', 'k_oz', 'k_no2', 'Tau_r']
      /scan_line_attributes
        Dimensions : {'number_of_lines': 1710}
        Variables  : ['year', 'day', 'msec', 'time', 'detnum', 'mside', 'slon', 'clon', 'elon', 'slat', 'clat', 'elat', 'csol_z']
      /geophysical_data
        Dimensions : {'number_of_lines': 1710, 'pixels_per_line': 1272, 'wavelength_3d': 172}
        Variables  : ['Rrs', 'Rrs_unc', 'aot_865', 'angstrom', 'avw', 'nflh', 'l2_flags']
      /navigation_data
        Dimensions : {'number_of_lines': 1710, 'pixels_per_line': 1272}
        Variables  : ['longitude', 'latitude', 'tilt']
      /processing_control
        Dimensions : {}
        Variables  : []
      /processing_control/input_parameters
        Dimensions : {}
        Variables  : []
      /processing_control/flag_percentages
        Dimensions : {}
        Variables  : []


## Get the matchups using that plan


```python
%%time
res = pc.matchup(plan[0:5], geometry="swath", variables=["Rrs"])
res
```

    CPU times: user 10.8 s, sys: 806 ms, total: 11.7 s
    Wall time: 18.8 s





<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>lat</th>
      <th>lon</th>
      <th>time</th>
      <th>granule_id</th>
      <th>Rrs_346</th>
      <th>Rrs_348</th>
      <th>Rrs_351</th>
      <th>Rrs_353</th>
      <th>Rrs_356</th>
      <th>Rrs_358</th>
      <th>...</th>
      <th>Rrs_706</th>
      <th>Rrs_707</th>
      <th>Rrs_708</th>
      <th>Rrs_709</th>
      <th>Rrs_711</th>
      <th>Rrs_712</th>
      <th>Rrs_713</th>
      <th>Rrs_714</th>
      <th>Rrs_717</th>
      <th>Rrs_719</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>27.3835</td>
      <td>-82.7375</td>
      <td>2024-06-13 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>27.3835</td>
      <td>-82.7375</td>
      <td>2024-06-13 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>27.1190</td>
      <td>-82.7125</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>0.01299</td>
      <td>0.012946</td>
      <td>0.013148</td>
      <td>0.013172</td>
      <td>0.012918</td>
      <td>0.012968</td>
      <td>...</td>
      <td>0.000238</td>
      <td>0.000228</td>
      <td>0.000198</td>
      <td>0.000194</td>
      <td>0.000186</td>
      <td>0.000172</td>
      <td>0.000152</td>
      <td>0.000122</td>
      <td>0.000108</td>
      <td>0.000094</td>
    </tr>
    <tr>
      <th>3</th>
      <td>26.9435</td>
      <td>-82.8170</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>26.6875</td>
      <td>-82.8065</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>5</th>
      <td>26.6675</td>
      <td>-82.6455</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
<p>6 rows × 176 columns</p>
</div>




```python

```
