"""Example 2 — multi-file temporal routing.

Demonstrates that the matchup engine automatically routes each
observation point to the granule whose temporal coverage contains
that point's date, opening only the necessary files.

Run::

    python -m examples.multi_file
    # or
    python examples/multi_file.py

What it shows
-------------
* Points spread across three different time periods (daily, 8-day,
  monthly).
* Three source granules, one for each period.
* The engine skips granules that have no overlapping points, meaning
  only one file is opened per point — even when the source list is long.
* How to mix granule types (daily, 8-day, monthly) in a single call.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

import earthaccess_matchup as eam
from examples._fixtures import make_8day, make_daily, make_monthly

# ---------------------------------------------------------------------------
# 1. Build a points table that spans multiple time periods.
# ---------------------------------------------------------------------------
df_points = pd.DataFrame(
    {
        "lat": [20.0, 20.0, 20.0, -30.0, -30.0],
        "lon": [10.0, 10.0, 10.0, 120.0, 120.0],
        "time": pd.to_datetime(
            [
                "2023-06-01",  # daily granule
                "2023-06-04",  # 8-day composite (2023-06-01 → 2023-06-08)
                "2023-06-15",  # monthly composite (June 2023)
                "2023-06-01",  # daily granule (different location)
                "2023-06-20",  # monthly composite (different location)
            ]
        ),
        "label": ["daily", "8day", "monthly", "daily-B", "monthly-B"],
    }
)

print("Input points:")
print(df_points.to_string(index=False))
print()

# ---------------------------------------------------------------------------
# 2. Prepare source files (three granule types for June 2023).
# ---------------------------------------------------------------------------
sources = [
    make_daily("20230601", seed=10),
    make_8day("20230601", "20230608", seed=20),
    make_monthly(2023, 6, seed=30),
]

print("Source files:")
for s in sources:
    print(f"  {Path(s).name}")
print()

# ---------------------------------------------------------------------------
# 3. Run matchup.
# ---------------------------------------------------------------------------
result, report = eam.matchup(
    df_points,
    sources,
    variables=["sst", "chlor_a"],
    engine="netcdf4",
    return_diagnostics=True,
)

# ---------------------------------------------------------------------------
# 4. Inspect results and diagnostics.
# ---------------------------------------------------------------------------
print("Matchup result:")
print(result.to_string(index=False))
print()
print("Diagnostics summary:")
print(f"  {report.summary()}")
print()
print("Per-granule breakdown:")
for g in report.granules:
    status = "OK" if g.succeeded else f"ERROR: {g.error}"
    print(f"  [{status}] {g.granule_id}")
    print(f"           found={g.variables_found}  missing={g.variables_missing}")
