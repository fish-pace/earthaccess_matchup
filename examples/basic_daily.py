"""Example 1 — basic daily matchup.

Demonstrates the simplest possible use-case: a handful of observation
points spread over a single day, matched against one daily L3 granule.

Run::

    python -m examples.basic_daily
    # or
    python examples/basic_daily.py

What it shows
-------------
* Building a minimal ``df_points`` DataFrame manually.
* Calling ``eam.matchup()`` with a list of local file paths (no
  ``earthaccess`` authentication required for offline testing).
* Inspecting the returned DataFrame.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running directly from the repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

import earthaccess_matchup as eam
from examples._fixtures import make_daily

# ---------------------------------------------------------------------------
# 1. Build a small points table (lat / lon / time).
# ---------------------------------------------------------------------------
df_points = pd.DataFrame(
    {
        "lat": [0.0, 30.0, 45.5, -15.2, 60.0],
        "lon": [-150.0, -90.0, 20.0, 45.0, 10.0],
        "time": pd.to_datetime(
            ["2023-06-01", "2023-06-01", "2023-06-01", "2023-06-01", "2023-06-01"]
        ),
        "station_id": ["S1", "S2", "S3", "S4", "S5"],
    }
)

print("Input points:")
print(df_points.to_string(index=False))
print()

# ---------------------------------------------------------------------------
# 2. Prepare source files.
#    In real usage this would be:
#        results = earthaccess.search_data(short_name=..., temporal=(...))
#        sources = earthaccess.open(results)
#    Here we use a local synthetic fixture instead.
# ---------------------------------------------------------------------------
sources = [make_daily("20230601", seed=1)]

print(f"Source file: {sources[0]}")
print()

# ---------------------------------------------------------------------------
# 3. Run matchup.
# ---------------------------------------------------------------------------
result = eam.matchup(
    df_points,
    sources,
    variables=["sst", "chlor_a"],
    engine="netcdf4",
)

# ---------------------------------------------------------------------------
# 4. Inspect results.
# ---------------------------------------------------------------------------
print("Matchup result:")
print(result.to_string(index=False))
print()
print(f"Matched {result['sst'].notna().sum()} / {len(result)} points for 'sst'")
print(f"Matched {result['chlor_a'].notna().sum()} / {len(result)} points for 'chlor_a'")
