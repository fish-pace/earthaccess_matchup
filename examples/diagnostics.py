"""Example 3 — diagnostics and error handling.

Demonstrates the ``return_diagnostics=True`` mode, which returns a
:class:`~earthaccess_matchup.diagnostics.report.MatchupReport` alongside
the result DataFrame.  The report records timing, variables
found/missing, per-point warnings, and file-open errors.

Run::

    python -m examples.diagnostics
    # or
    python examples/diagnostics.py

What it shows
-------------
* Requesting a variable that exists and one that does not.
* Including a deliberately broken source file to trigger an error path.
* Reading the MatchupReport: total / succeeded / skipped counts, elapsed
  time, and per-granule details.
* How warnings surface when a point-level extraction fails gracefully.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

import earthaccess_matchup as eam
from examples._fixtures import FIXTURES_DIR, make_daily

# ---------------------------------------------------------------------------
# 1. Points table.
# ---------------------------------------------------------------------------
df_points = pd.DataFrame(
    {
        "lat": [45.0, -20.0, 70.0],
        "lon": [-60.0, 80.0, 30.0],
        "time": pd.to_datetime(["2023-07-15", "2023-07-15", "2023-07-15"]),
    }
)

print("Input points:")
print(df_points.to_string(index=False))
print()

# ---------------------------------------------------------------------------
# 2. Sources: one valid file + one deliberately broken file.
# ---------------------------------------------------------------------------
good_file = make_daily("20230715", seed=99)

bad_file = FIXTURES_DIR / "AQUA_MODIS.20230715.L3m.DAY.BROKEN.nc"
bad_file.write_bytes(b"not a valid netcdf file")  # intentionally corrupt

sources = [good_file, str(bad_file)]
print("Sources:")
for s in sources:
    print(f"  {Path(s).name}")
print()

# ---------------------------------------------------------------------------
# 3. Run matchup with diagnostics enabled.
#    Request 'sst' (present) and 'Rrs_443' (absent) to show the
#    variables_found / variables_missing tracking.
# ---------------------------------------------------------------------------
result, report = eam.matchup(
    df_points,
    sources,
    variables=["sst", "Rrs_443"],
    engine="netcdf4",
    return_diagnostics=True,
)

# ---------------------------------------------------------------------------
# 4. Print result DataFrame.
# ---------------------------------------------------------------------------
print("Matchup result:")
print(result.to_string(index=False))
print()

# ---------------------------------------------------------------------------
# 5. Print full diagnostics report.
# ---------------------------------------------------------------------------
print(f"Summary: {report.summary()}")
print()
print(f"  Total granules attempted : {report.total}")
print(f"  Succeeded                : {report.succeeded}")
print(f"  Skipped (errors)         : {report.skipped}")
print(f"  Wall-clock time          : {report.elapsed_seconds:.2f}s")
print()

for i, g in enumerate(report.granules, start=1):
    print(f"  Granule {i}: {g.granule_id}")
    print(f"    Succeeded         : {g.succeeded}")
    print(f"    Elapsed           : {g.elapsed_seconds:.3f}s")
    print(f"    Variables found   : {g.variables_found}")
    print(f"    Variables missing : {g.variables_missing}")
    if g.warnings:
        for w in g.warnings:
            print(f"    Warning           : {w}")
    if g.error:
        print(f"    Error             : {g.error}")
    print()
