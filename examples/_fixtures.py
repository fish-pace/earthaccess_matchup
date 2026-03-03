"""Fixture helpers shared by all examples.

Generates small synthetic L3 flat NetCDF files and writes them to the
``examples/fixtures/`` directory.  Files are regenerated only when
missing, so they persist between runs for iterative debugging.

Available fixtures
------------------
``make_daily(date_str)``
    Single daily file named ``AQUA_MODIS.<YYYYMMDD>.L3m.DAY.SST.sst.4km.nc``.
    Variables: ``sst``, ``chlor_a``.

``make_8day(start_str, end_str)``
    8-day composite named ``AQUA_MODIS.<start>_<end>.L3m.8D.SST.sst.4km.nc``.
    Variables: ``sst``, ``chlor_a``.

``make_monthly(year, month)``
    Monthly composite named ``AQUA_MODIS.<YYYYMMDD>_<YYYYMMDD>.L3m.MO.SST.sst.4km.nc``.
    Variables: ``sst``, ``chlor_a``.

All datasets use a 1° global grid (181 × 361 points) with ``lat`` /
``lon`` coordinates, matching the layout of real NASA L3m products.
"""

from __future__ import annotations

import calendar
from pathlib import Path

import numpy as np
import xarray as xr

# Directory where fixture files are written.
FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)

# Grid shared across all fixtures.
_LATS = np.arange(-90.0, 91.0, 1.0)
_LONS = np.arange(-180.0, 181.0, 1.0)


def _make_dataset(seed: int) -> xr.Dataset:
    rng = np.random.default_rng(seed)
    sst = rng.uniform(5.0, 35.0, (_LATS.size, _LONS.size)).astype(np.float32)
    chlor_a = rng.uniform(0.01, 5.0, (_LATS.size, _LONS.size)).astype(np.float32)
    return xr.Dataset(
        {
            "sst": (
                ["lat", "lon"],
                sst,
                {"units": "degrees_C", "long_name": "Sea Surface Temperature"},
            ),
            "chlor_a": (
                ["lat", "lon"],
                chlor_a,
                {"units": "mg m^-3", "long_name": "Chlorophyll Concentration"},
            ),
        },
        coords={"lat": _LATS, "lon": _LONS},
    )


def make_daily(date_str: str, *, seed: int = 42) -> str:
    """Return path to a daily fixture file, creating it if absent.

    Parameters
    ----------
    date_str:
        Date in ``YYYYMMDD`` format, e.g. ``"20230601"``.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    str
        Absolute path to the NetCDF file.
    """
    fname = f"AQUA_MODIS.{date_str}.L3m.DAY.SST.sst.4km.nc"
    path = FIXTURES_DIR / fname
    if not path.exists():
        _make_dataset(seed).to_netcdf(path)
    return str(path)


def make_8day(start_str: str, end_str: str, *, seed: int = 43) -> str:
    """Return path to an 8-day composite fixture, creating it if absent.

    Parameters
    ----------
    start_str, end_str:
        Start and end dates in ``YYYYMMDD`` format.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    str
        Absolute path to the NetCDF file.
    """
    fname = f"AQUA_MODIS.{start_str}_{end_str}.L3m.8D.SST.sst.4km.nc"
    path = FIXTURES_DIR / fname
    if not path.exists():
        _make_dataset(seed).to_netcdf(path)
    return str(path)


def make_monthly(year: int, month: int, *, seed: int = 44) -> str:
    """Return path to a monthly composite fixture, creating it if absent.

    Parameters
    ----------
    year, month:
        Calendar year and month (1-12).
    seed:
        Random seed for reproducibility.

    Returns
    -------
    str
        Absolute path to the NetCDF file.
    """
    last_day = calendar.monthrange(year, month)[1]
    start_str = f"{year}{month:02d}01"
    end_str = f"{year}{month:02d}{last_day:02d}"
    fname = f"AQUA_MODIS.{start_str}_{end_str}.L3m.MO.SST.sst.4km.nc"
    path = FIXTURES_DIR / fname
    if not path.exists():
        _make_dataset(seed).to_netcdf(path)
    return str(path)
