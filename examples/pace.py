"""Example  — PACE.


Run::

    python -m examplespace

What it shows
-------------
* Get some PACE matchups
* Requires earthdata auth
"""

from pathlib import Path
import earthaccess
import earthaccess_matchup as eam
import pandas as pd

HERE = Path(__file__).resolve().parent
POINTS_CSV = HERE / "fixtures" / "points.csv"

earthaccess.login()
df_points = pd.read_csv(POINTS_CSV)  # lat, lon, date columns

result = eam.matchup(
    df_points[0:2],
    data_source="earthaccess",
    short_name="PACE_OCI_L3M_RRS",
    granule_name="*.DAY.*.4km.*",
    variables=["Rrs"],
)

print(result)