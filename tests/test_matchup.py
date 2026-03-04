"""Integration tests for the matchup engine using synthetic NetCDF data."""

from __future__ import annotations

import math
import pathlib
import unittest.mock as mock

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from point_collocation.core._granule import get_source_id, parse_temporal_range
from point_collocation.core.engine import _process_single_granule
from point_collocation.core.plan import GranuleMeta

# ---------------------------------------------------------------------------
# Tests for get_source_id
# ---------------------------------------------------------------------------

class TestGetSourceId:
    def test_string_path(self) -> None:
        assert get_source_id("/data/AQUA_MODIS.20230601.nc") == "AQUA_MODIS.20230601.nc"

    def test_basename_string(self) -> None:
        assert get_source_id("AQUA_MODIS.20230601.nc") == "AQUA_MODIS.20230601.nc"

    def test_pathlib_path(self, tmp_path: pathlib.Path) -> None:
        p = pathlib.Path("/some/path/file.nc")
        assert get_source_id(p) == "file.nc"

    def test_object_with_path_attr(self) -> None:
        class FakeFSFile:
            path = "/s3/bucket/AQUA_MODIS.20230601.nc"

        assert get_source_id(FakeFSFile()) == "AQUA_MODIS.20230601.nc"

    def test_object_with_name_attr(self) -> None:
        class FakeFSFile:
            name = "AQUA_MODIS.20230601.nc"

        assert get_source_id(FakeFSFile()) == "AQUA_MODIS.20230601.nc"

    def test_fallback_to_str(self) -> None:
        result = get_source_id(42)
        assert result == "42"


# ---------------------------------------------------------------------------
# Tests for parse_temporal_range
# ---------------------------------------------------------------------------

class TestParseTemporalRange:
    def test_daily_calendar_format(self) -> None:
        start, end = parse_temporal_range("AQUA_MODIS.20230601.L3m.DAY.SST.sst.4km.nc")
        assert start == pd.Timestamp("2023-06-01")
        assert end == pd.Timestamp("2023-06-01")

    def test_daily_doy_format(self) -> None:
        # 2024-DOY-070 = 2024-03-10
        start, end = parse_temporal_range("PACE_OCI_2024070.L3m.DAY.RRS.Rrs_412.4km.nc")
        assert start == pd.Timestamp("2024-03-10")
        assert end == pd.Timestamp("2024-03-10")

    def test_eight_day_calendar_pair(self) -> None:
        start, end = parse_temporal_range(
            "AQUA_MODIS.20230601_20230608.L3m.8D.SST.sst.4km.nc"
        )
        assert start == pd.Timestamp("2023-06-01")
        assert end == pd.Timestamp("2023-06-08")

    def test_eight_day_doy_pair(self) -> None:
        # DOY 049 = 2024-02-18, DOY 056 = 2024-02-25
        start, end = parse_temporal_range(
            "PACE_OCI_2024049_2024056.L3m.8D.CHL.chlor_a.9km.nc"
        )
        assert start == pd.Timestamp("2024-02-18")
        assert end == pd.Timestamp("2024-02-25")

    def test_monthly_calendar_pair(self) -> None:
        start, end = parse_temporal_range(
            "AQUA_MODIS.20230601_20230630.L3m.MO.CHL.chlor_a.9km.nc"
        )
        assert start == pd.Timestamp("2023-06-01")
        assert end == pd.Timestamp("2023-06-30")

    def test_single_doy_with_8d_token(self) -> None:
        # DOY 049 of 2024 = 2024-02-18; +7 days = 2024-02-25
        start, end = parse_temporal_range("PRODUCT_2024049.L3m.8D.CHL.nc")
        assert start == pd.Timestamp("2024-02-18")
        assert end == pd.Timestamp("2024-02-25")

    def test_single_doy_with_mo_token(self) -> None:
        start, end = parse_temporal_range("PRODUCT_2024032.L3m.MO.CHL.nc")
        # DOY 032 = 2024-02-01; end of Feb 2024 = 29 (leap year)
        assert start == pd.Timestamp("2024-02-01")
        assert end == pd.Timestamp("2024-02-29")

    def test_raises_on_unrecognised_name(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_temporal_range("nodate_here.nc")

    def test_basename_extracted_from_full_path(self) -> None:
        start, end = parse_temporal_range(
            "/some/long/path/AQUA_MODIS.20230601.L3m.DAY.SST.sst.4km.nc"
        )
        assert start == pd.Timestamp("2023-06-01")
        assert end == pd.Timestamp("2023-06-01")


# ---------------------------------------------------------------------------
# Tests for _process_single_granule (memory-isolation subfunction)
# ---------------------------------------------------------------------------

def _make_fake_granule_meta(granule_id: str = "https://example.com/g.nc") -> GranuleMeta:
    return GranuleMeta(
        granule_id=granule_id,
        begin=pd.Timestamp("2023-06-01T00:00:00"),
        end=pd.Timestamp("2023-06-01T23:59:59"),
        bbox=(-180.0, -90.0, 180.0, 90.0),
        result_index=0,
    )


def _make_fake_dataset(lat_vals: list, lon_vals: list) -> xr.Dataset:
    """Create a minimal in-memory xarray Dataset with a 'sst' variable."""
    lats = np.array(lat_vals, dtype=float)
    lons = np.array(lon_vals, dtype=float)
    rng = np.random.default_rng(0)
    data = rng.random((len(lats), len(lons))).astype(float)
    return xr.Dataset(
        {"sst": (["lat", "lon"], data)},
        coords={"lat": lats, "lon": lons},
    )


class TestProcessSingleGranule:
    """Unit tests for the _process_single_granule memory-isolation subfunction."""

    def _make_points(self, lats: list, lons: list) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "lat": lats,
                "lon": lons,
                "time": pd.to_datetime(["2023-06-01T12:00:00"] * len(lats)),
            }
        )

    def test_returns_list_of_dicts(self) -> None:
        """_process_single_granule must return a list of row dicts."""
        ds = _make_fake_dataset([-90.0, 0.0, 90.0], [-180.0, 0.0, 180.0])
        points = self._make_points([0.0], [0.0])
        gm = _make_fake_granule_meta()

        ctx = mock.MagicMock()
        ctx.__enter__ = mock.Mock(return_value=ds)
        ctx.__exit__ = mock.Mock(return_value=False)
        with mock.patch("xarray.open_dataset", return_value=ctx):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0],
                gm=gm,
                variables=["sst"],
                points=points,
                kwargs={},
            )

        assert isinstance(rows, list)
        assert len(rows) == 1
        assert "granule_id" in rows[0]
        assert rows[0]["granule_id"] == "https://example.com/g.nc"

    def test_extracts_scalar_variable(self) -> None:
        """Scalar variable values must be numeric (not NaN) when the variable exists."""
        ds = _make_fake_dataset([-90.0, 0.0, 90.0], [-180.0, 0.0, 180.0])
        points = self._make_points([0.0], [0.0])
        gm = _make_fake_granule_meta()

        ctx = mock.MagicMock()
        ctx.__enter__ = mock.Mock(return_value=ds)
        ctx.__exit__ = mock.Mock(return_value=False)
        with mock.patch("xarray.open_dataset", return_value=ctx):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0],
                gm=gm,
                variables=["sst"],
                points=points,
                kwargs={},
            )

        assert len(rows) == 1
        assert not math.isnan(rows[0]["sst"])

    def test_missing_variable_produces_nan(self) -> None:
        """A requested variable not present in the dataset must produce NaN."""
        ds = _make_fake_dataset([-90.0, 0.0, 90.0], [-180.0, 0.0, 180.0])
        points = self._make_points([0.0], [0.0])
        gm = _make_fake_granule_meta()

        ctx = mock.MagicMock()
        ctx.__enter__ = mock.Mock(return_value=ds)
        ctx.__exit__ = mock.Mock(return_value=False)
        with mock.patch("xarray.open_dataset", return_value=ctx):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0],
                gm=gm,
                variables=["no_such_var"],
                points=points,
                kwargs={},
            )

        assert len(rows) == 1
        assert math.isnan(rows[0]["no_such_var"])

    def test_multiple_points_multiple_rows(self) -> None:
        """Each point index must produce exactly one row in the output."""
        ds = _make_fake_dataset([-90.0, 0.0, 90.0], [-180.0, 0.0, 180.0])
        points = self._make_points([0.0, 90.0, -90.0], [0.0, 180.0, -180.0])
        gm = _make_fake_granule_meta()

        ctx = mock.MagicMock()
        ctx.__enter__ = mock.Mock(return_value=ds)
        ctx.__exit__ = mock.Mock(return_value=False)
        with mock.patch("xarray.open_dataset", return_value=ctx):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0, 1, 2],
                gm=gm,
                variables=["sst"],
                points=points,
                kwargs={},
            )

        assert len(rows) == 3
        for row in rows:
            assert row["granule_id"] == "https://example.com/g.nc"

    def test_open_failure_produces_nan_rows(self) -> None:
        """When xr.open_dataset raises, NaN rows must be returned (not propagated)."""
        points = self._make_points([0.0], [0.0])
        gm = _make_fake_granule_meta()

        with mock.patch("xarray.open_dataset", side_effect=OSError("cannot open")):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0],
                gm=gm,
                variables=["sst"],
                points=points,
                kwargs={},
            )

        assert len(rows) == 1
        assert math.isnan(rows[0]["sst"])
        assert rows[0]["granule_id"] == "https://example.com/g.nc"

    def test_granule_id_set_on_all_rows(self) -> None:
        """All output rows must carry the correct granule_id from the GranuleMeta."""
        ds = _make_fake_dataset([-90.0, 0.0, 90.0], [-180.0, 0.0, 180.0])
        points = self._make_points([0.0, 0.0], [0.0, 0.0])
        gm = _make_fake_granule_meta(granule_id="https://custom.example/g.nc")

        ctx = mock.MagicMock()
        ctx.__enter__ = mock.Mock(return_value=ds)
        ctx.__exit__ = mock.Mock(return_value=False)
        with mock.patch("xarray.open_dataset", return_value=ctx):
            rows = _process_single_granule(
                file_obj=object(),
                pt_indices=[0, 1],
                gm=gm,
                variables=["sst"],
                points=points,
                kwargs={},
            )

        assert all(r["granule_id"] == "https://custom.example/g.nc" for r in rows)
