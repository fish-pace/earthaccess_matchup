# Basic matchups with PACE data

```
import point_collocation as pc
```

* Create a plan for files to use `pc.plan()`
* Print the plan to check it `print(plan.summary())`
* Do the plan and get matchups `pc.matchup(plan, geometry="grid")`

## Read in some points


```python
import pandas as pd
time = "2025-04-09"
lat = 30.0
lon = -89.0

df = pd.DataFrame(
    {
        "lat": [lat],
        "lon": [lon],
        "time": [time],
    }
)
df["time"] = pd.to_datetime(df["time"])
```

## Create a plan


```python
%%time
import point_collocation as pc
plan = pc.plan(
    df,
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L3M_Rrs",
        "granule_name": "*.8D.*.4km.*",
    }
)
```

    CPU times: user 18.7 ms, sys: 219 μs, total: 18.9 ms
    Wall time: 16.6 s


### Look at variables in that dataset


```python
plan.show_variables(geometry="grid")
```

    Dimensions : {'lat': 4320, 'lon': 8640, 'wavelength': 172, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['Rrs', 'palette']



```python
plan.summary()
```

    Plan: 1 points → 1 unique granule(s)
      Points with 0 matches : 0
      Points with >1 matches: 0
      Variables  : []
      Time buffer: 0 days 00:00:00
    
    First 1 point(s):
      [0] lat=30.0000, lon=-89.0000, time=2025-04-09 00:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250407_20250414.L3m.8D.RRS.V3_1.Rrs.4km.nc


## Get the matchups

For variables with a 3rd dimension, like wavelength, all variables will be shown with `_3rd dim value`.


```python
res = pc.matchup(plan, geometry="grid", variables=["Rrs"])
res
```




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
      <td>30.0</td>
      <td>-89.0</td>
      <td>2025-04-09</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>0.000306</td>
      <td>0.000488</td>
      <td>0.00065</td>
      <td>0.000656</td>
      <td>0.000726</td>
      <td>0.000932</td>
      <td>...</td>
      <td>0.003598</td>
      <td>0.003496</td>
      <td>0.003386</td>
      <td>0.003268</td>
      <td>0.003138</td>
      <td>0.003004</td>
      <td>0.00286</td>
      <td>0.002662</td>
      <td>0.002098</td>
      <td>0.001644</td>
    </tr>
  </tbody>
</table>
<p>1 rows × 176 columns</p>
</div>



### Datasets with only lat, lon

In this case, just the variable appears.


```python
%%time
import point_collocation as pc
plan = pc.plan(
    df,
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L3M_AVW",
        "granule_name": "*.DAY.*.4km.*",
    }
)
res = pc.matchup(plan, geometry="grid", variables=["avw"])
res
```

    CPU times: user 8.32 ms, sys: 11 ms, total: 19.3 ms
    Wall time: 9.02 s


## Plan with many files

If you are not sure what files to use, you can use a short name without `granule_name`. Then look at the plan summary to see the file names. You just need to look at one file (`n=1`). In this example, there are 16 files that match. 2 resolutions (4km and 0.1 deg) and 8 temporal resolutions:

* `R32`: rolling 32 days starting every 7 days, 4 dates
* `SNSP`: seasonal/quarterly
* `8D`: 8 day
* `DAY`: daily
* `MO`: monthly starting 1st day of each month to last


```python
import point_collocation as pc
plan = pc.plan(
    df,
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L3M_AVW",
    }
)
```


```python
plan.summary(n=1)
```

    Plan: 1 points → 16 unique granule(s)
      Points with 0 matches : 0
      Points with >1 matches: 1
      Variables  : []
      Time buffer: 0 days 00:00:00
    
    First 1 point(s):
      [0] lat=30.0000, lon=-89.0000, time=2025-04-09 00:00:00: 16 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250314_20250414.L3m.R32.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250314_20250414.L3m.R32.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250321_20250620.L3m.SNSP.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250321_20250620.L3m.SNSP.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250322_20250422.L3m.R32.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250322_20250422.L3m.R32.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250330_20250430.L3m.R32.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250330_20250430.L3m.R32.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250401_20250430.L3m.MO.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250401_20250430.L3m.MO.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250407_20250414.L3m.8D.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250407_20250414.L3m.8D.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250407_20250508.L3m.R32.AVW.V3_1.avw.4km.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250407_20250508.L3m.R32.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250409.L3m.DAY.AVW.V3_1.avw.0p1deg.nc
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250409.L3m.DAY.AVW.V3_1.avw.4km.nc


### Filter to the files you want

Once you see the files names, you can filter to the ones you want. using `granule_name`. For example `*.SNSP.*.4km.*` to get the seasonal (quarterly) values. `*` are wildcard values.


```python
import point_collocation as pc
plan = pc.plan(
    df,
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L3M_AVW",
        "granule_name": "*.SNSP.*.4km.*"
    }
)
```


```python
plan.summary()
```

    Plan: 1 points → 1 unique granule(s)
      Points with 0 matches : 0
      Points with >1 matches: 0
      Variables  : []
      Time buffer: 0 days 00:00:00
    
    First 1 point(s):
      [0] lat=30.0000, lon=-89.0000, time=2025-04-09 00:00:00: 1 match(es)
        → https://obdaac-tea.earthdatacloud.nasa.gov/ob-cumulus-prod-public/PACE_OCI.20250321_20250620.L3m.SNSP.AVW.V3_1.avw.4km.nc


## Try many points


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
import earthaccess
import point_collocation as pc

earthaccess.login()

plan = pc.plan(
    df_points[0:100],
    data_source="earthaccess",
    source_kwargs={
        "short_name": "PACE_OCI_L3M_AVW",
        "granule_name": "*.DAY.*.4km.*",
    }
)
```

    CPU times: user 172 ms, sys: 17 ms, total: 189 ms
    Wall time: 11.2 s



```python
plan.summary(n=0)
```

    Plan: 100 points → 131 unique granule(s)
      Points with 0 matches : 0
      Points with >1 matches: 0
      Variables  : []
      Time buffer: 0 days 00:00:00


## Get 100 matchups using that plan


```python
%%time
res = pc.matchup(plan[0:100], geometry="grid", variables = ["avw"])
```

    CPU times: user 3.76 s, sys: 446 ms, total: 4.2 s
    Wall time: 11.7 s



```python
res.head()
```




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
      <th>avw</th>
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
    </tr>
    <tr>
      <th>1</th>
      <td>27.1190</td>
      <td>-82.7125</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>26.9435</td>
      <td>-82.8170</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>3</th>
      <td>26.6875</td>
      <td>-82.8065</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>26.6675</td>
      <td>-82.6455</td>
      <td>2024-06-14 12:00:00</td>
      <td>https://obdaac-tea.earthdatacloud.nasa.gov/ob-...</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



## Try lots of products

Pick a recent data point so NRT works. Not all products have files.


```python
import pandas as pd
time = "2026-01-09"
lat = 30.0
lon = -89.0

df = pd.DataFrame(
    {
        "lat": [lat],
        "lon": [lon],
        "time": [time],
    }
)
df["time"] = pd.to_datetime(df["time"])
```


```python
import earthaccess
results = earthaccess.search_datasets(instrument="oci")

short_names = [
    item.summary()["short-name"]
    for item in results
    if "L3M" in item.summary()["short-name"]
]

print(short_names)
```

    ['PACE_OCI_L3M_UVAI_UAA_NRT', 'PACE_OCI_L3M_UVAI_UAA', 'PACE_OCI_L3M_AER_UAA_NRT', 'PACE_OCI_L3M_AER_UAA', 'PACE_OCI_L3M_AOT_NRT', 'PACE_OCI_L3M_AOT', 'PACE_OCI_L3M_AVW_NRT', 'PACE_OCI_L3M_AVW', 'PACE_OCI_L3M_CHL_NRT', 'PACE_OCI_L3M_CHL', 'PACE_OCI_L3M_CLOUD_MASK_NRT', 'PACE_OCI_L3M_CLOUD_MASK', 'PACE_OCI_L3M_CLOUD_NRT', 'PACE_OCI_L3M_CLOUD', 'PACE_OCI_L3M_KD_NRT', 'PACE_OCI_L3M_KD', 'PACE_OCI_L3M_FLH_NRT', 'PACE_OCI_L3M_FLH', 'PACE_OCI_L3M_LANDVI_NRT', 'PACE_OCI_L3M_LANDVI', 'PACE_OCI_L3M_IOP_NRT', 'PACE_OCI_L3M_IOP', 'PACE_OCI_L3M_PIC_NRT', 'PACE_OCI_L3M_PIC', 'PACE_OCI_L3M_POC_NRT', 'PACE_OCI_L3M_POC', 'PACE_OCI_L3M_PAR_NRT', 'PACE_OCI_L3M_PAR', 'PACE_OCI_L3M_CARBON', 'PACE_OCI_L3M_CARBON_NRT', 'PACE_OCI_L3M_RRS_NRT', 'PACE_OCI_L3M_RRS', 'PACE_OCI_L3M_SFREFL_NRT', 'PACE_OCI_L3M_SFREFL', 'PACE_OCI_L3M_TRGAS_NRT', 'PACE_OCI_L3M_TRGAS']



```python
%%time
import point_collocation as pc
for short_name in short_names:
    print(f"\n===== {short_name} =====")
    
    try:
        plan = pc.plan(
            df,
            data_source="earthaccess",
            source_kwargs={
                "short_name": short_name,
                "granule_name":"*.DAY.*",
             }
        )
        plan.show_variables(geometry="grid")
    except Exception as e:
        print("Failed:", e)
```

    
    ===== PACE_OCI_L3M_UVAI_UAA_NRT =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_UVAI_UAA =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_AER_UAA_NRT =====
    Dimensions : {'lat': 180, 'lon': 360}
    Variables  : ['Aerosol_Optical_Depth_354', 'Aerosol_Optical_Depth_388', 'Aerosol_Optical_Depth_480', 'Aerosol_Optical_Depth_550', 'Aerosol_Optical_Depth_670', 'Aerosol_Optical_Depth_870', 'Aerosol_Optical_Depth_1240', 'Aerosol_Optical_Depth_2200', 'Optical_Depth_Ratio_Small_Ocean_used', 'NUV_AerosolCorrCloudOpticalDepth', 'NUV_AerosolOpticalDepthOverCloud_354', 'NUV_AerosolOpticalDepthOverCloud_388', 'NUV_AerosolOpticalDepthOverCloud_550', 'NUV_AerosolIndex', 'NUV_CloudOpticalDepth', 'AAOD_354', 'AAOD_388', 'AAOD_550']
    
    ===== PACE_OCI_L3M_AER_UAA =====
    Dimensions : {'lat': 180, 'lon': 360}
    Variables  : ['Aerosol_Optical_Depth_354', 'Aerosol_Optical_Depth_388', 'Aerosol_Optical_Depth_480', 'Aerosol_Optical_Depth_550', 'Aerosol_Optical_Depth_670', 'Aerosol_Optical_Depth_870', 'Aerosol_Optical_Depth_1240', 'Aerosol_Optical_Depth_2200', 'Optical_Depth_Ratio_Small_Ocean_used', 'NUV_AerosolCorrCloudOpticalDepth', 'NUV_AerosolOpticalDepthOverCloud_354', 'NUV_AerosolOpticalDepthOverCloud_388', 'NUV_AerosolOpticalDepthOverCloud_550', 'NUV_AerosolIndex', 'NUV_CloudOpticalDepth', 'AAOD_354', 'AAOD_388', 'AAOD_550']
    
    ===== PACE_OCI_L3M_AOT_NRT =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_AOT =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_AVW_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['avw', 'palette']
    
    ===== PACE_OCI_L3M_AVW =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['avw', 'palette']
    
    ===== PACE_OCI_L3M_CHL_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['chlor_a', 'palette']
    
    ===== PACE_OCI_L3M_CHL =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['chlor_a', 'palette']
    
    ===== PACE_OCI_L3M_CLOUD_MASK_NRT =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_CLOUD_MASK =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_CLOUD_NRT =====
    Dimensions : {'lat': 180, 'lon': 360}
    Variables  : ['cloud_fraction', 'ice_cloud_fraction', 'water_cloud_fraction', 'ctt', 'ctp', 'cth', 'cth_cot', 'cth_alb', 'ctt_water', 'ctp_water', 'cth_water', 'cth_cot_water', 'cth_alb_water', 'ctt_ice', 'ctp_ice', 'cth_ice', 'cth_cot_ice', 'cth_alb_ice', 'cer_16', 'cot_16', 'cwp_16', 'cer_16_water', 'cot_16_water', 'cwp_16_water', 'cer_16_ice', 'cot_16_ice', 'cwp_16_ice', 'cer_21', 'cot_21', 'cwp_21', 'cer_21_water', 'cot_21_water', 'cwp_21_water', 'cer_21_ice', 'cot_21_ice', 'cwp_21_ice', 'cer_22', 'cot_22', 'cwp_22', 'cer_22_water', 'cot_22_water', 'cwp_22_water', 'cer_22_ice', 'cot_22_ice', 'cwp_22_ice']
    
    ===== PACE_OCI_L3M_CLOUD =====
    Dimensions : {'lat': 180, 'lon': 360}
    Variables  : ['cloud_fraction', 'ice_cloud_fraction', 'water_cloud_fraction', 'ctt', 'ctp', 'cth', 'cth_cot', 'cth_alb', 'ctt_water', 'ctp_water', 'cth_water', 'cth_cot_water', 'cth_alb_water', 'ctt_ice', 'ctp_ice', 'cth_ice', 'cth_cot_ice', 'cth_alb_ice', 'cer_16', 'cot_16', 'cwp_16', 'cer_16_water', 'cot_16_water', 'cwp_16_water', 'cer_16_ice', 'cot_16_ice', 'cwp_16_ice', 'cer_21', 'cot_21', 'cwp_21', 'cer_21_water', 'cot_21_water', 'cwp_21_water', 'cer_21_ice', 'cot_21_ice', 'cwp_21_ice', 'cer_22', 'cot_22', 'cwp_22', 'cer_22_water', 'cot_22_water', 'cwp_22_water', 'cer_22_ice', 'cot_22_ice', 'cwp_22_ice']
    
    ===== PACE_OCI_L3M_KD_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'wavelength': 17, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['Kd', 'palette']
    
    ===== PACE_OCI_L3M_KD =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'wavelength': 17, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['Kd', 'palette']
    
    ===== PACE_OCI_L3M_FLH_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['nflh', 'palette']
    
    ===== PACE_OCI_L3M_FLH =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['nflh', 'palette']
    
    ===== PACE_OCI_L3M_LANDVI_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['ndvi', 'evi', 'ndwi', 'ndii', 'cci', 'ndsi', 'pri', 'cire', 'car', 'mari', 'palette']
    
    ===== PACE_OCI_L3M_LANDVI =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['ndvi', 'evi', 'ndwi', 'ndii', 'cci', 'ndsi', 'pri', 'cire', 'car', 'mari', 'palette']
    
    ===== PACE_OCI_L3M_IOP_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['adg_s', 'palette']
    
    ===== PACE_OCI_L3M_IOP =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['adg_442', 'palette']
    
    ===== PACE_OCI_L3M_PIC_NRT =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_PIC =====
    Failed: No granules in plan — cannot show variables.
    
    ===== PACE_OCI_L3M_POC_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['poc', 'palette']
    
    ===== PACE_OCI_L3M_POC =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['poc', 'palette']
    
    ===== PACE_OCI_L3M_PAR_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['par_day_scalar_below', 'par_day_planar_above', 'par_day_planar_below', 'ipar_planar_above', 'ipar_planar_below', 'ipar_scalar_below', 'palette']
    
    ===== PACE_OCI_L3M_PAR =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['par_day_scalar_below', 'par_day_planar_above', 'par_day_planar_below', 'ipar_planar_above', 'ipar_planar_below', 'ipar_scalar_below', 'palette']
    
    ===== PACE_OCI_L3M_CARBON =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['carbon_phyto', 'palette']
    
    ===== PACE_OCI_L3M_CARBON_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['carbon_phyto', 'palette']
    
    ===== PACE_OCI_L3M_RRS_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'wavelength': 172, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['Rrs', 'palette']
    
    ===== PACE_OCI_L3M_RRS =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'wavelength': 172, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['Rrs', 'palette']
    
    ===== PACE_OCI_L3M_SFREFL_NRT =====
    Dimensions : {'lat': 4320, 'lon': 8640, 'wavelength': 122, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['rhos', 'palette']
    
    ===== PACE_OCI_L3M_SFREFL =====
    Dimensions : {'lat': 1800, 'lon': 3600, 'wavelength': 122, 'rgb': 3, 'eightbitcolor': 256}
    Variables  : ['rhos', 'palette']
    
    ===== PACE_OCI_L3M_TRGAS_NRT =====
    Dimensions : {'lat': 1800, 'lon': 3600}
    Variables  : ['total_column_o3', 'total_column_no2']
    
    ===== PACE_OCI_L3M_TRGAS =====
    Dimensions : {'lat': 1800, 'lon': 3600}
    Variables  : ['total_column_o3', 'total_column_no2']
    CPU times: user 2.96 s, sys: 279 ms, total: 3.24 s
    Wall time: 55.6 s



```python

```
