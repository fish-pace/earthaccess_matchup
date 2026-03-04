"""Integration tests for the matchup engine using synthetic NetCDF data."""

from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from point_collocation.core._granule import get_source_id, parse_temporal_range

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
