"""Core matchup engine — no earthaccess dependency here.

Responsibilities
----------------
* Accept a :class:`~point_collocation.core.plan.Plan` object built with
  :func:`~point_collocation.plan`.
* Open each granule individually with ``xarray.open_dataset`` (never
  ``open_mfdataset``) to minimise cloud I/O and avoid memory leaks.
* Extract the requested variables at each point's location/time using
  nearest-neighbour selection.
* Collect results into a ``pandas.DataFrame`` with one row per
  (point, granule) pair.

The engine does **not** know about earthaccess, STAC, or any other
cloud-data provider.  All provider-specific logic lives in
``point_collocation.adapters``.

Future extension points
-----------------------
* ``pre_extract`` hook — spatial averaging, neighbourhood selection
* ``post_extract`` hook — QA filtering, unit conversion
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
import xarray as xr

if TYPE_CHECKING:
    from point_collocation.core.plan import GranuleMeta, Plan

# Candidate coordinate names tried in order when locating lat/lon dims.
_LAT_NAMES = ("lat", "latitude", "Latitude", "LAT")
_LON_NAMES = ("lon", "longitude", "Longitude", "LON")


def matchup(
    plan: "Plan",
    **open_dataset_kwargs: object,
) -> pd.DataFrame:
    """Extract variables from cloud-hosted granules at the given points.

    Parameters
    ----------
    plan:
        A :class:`~point_collocation.core.plan.Plan` object previously
        built with :func:`~point_collocation.plan`.  Variables,
        data source, and search parameters are all taken from the plan.
        One output row is produced per (point, granule) pair; points
        with zero matching granules produce a single NaN row.
    **open_dataset_kwargs:
        Extra keyword arguments forwarded to ``xarray.open_dataset`` for
        every granule opened during the run.  Defaults to
        ``engine="h5netcdf"`` when no ``engine`` key is provided.

    Returns
    -------
    pandas.DataFrame
        One row per (point, granule) pair, including a ``granule_id``
        column and one column per variable in the plan.  Points with
        zero matching granules contribute a single NaN row.
    """
    return _execute_plan(plan, variables=plan.variables, **open_dataset_kwargs)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _execute_plan(
    plan: "Plan",
    *,
    variables: list[str],
    **open_dataset_kwargs: object,
) -> pd.DataFrame:
    """Execute a :class:`~point_collocation.core.plan.Plan`.

    Opens each granule once and extracts variable values for all points
    mapped to it.  Returns one row per (point, granule) pair; points
    with zero granule matches get a single NaN row.
    """
    try:
        import earthaccess  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "The 'earthaccess' package is required to execute a Plan. "
            "Install it with: pip install earthaccess"
        ) from exc

    opened_files: list[object] = earthaccess.open(plan.results, pqdm_kwargs={"disable": True})

    kwargs = dict(open_dataset_kwargs)
    if "engine" not in kwargs:
        kwargs["engine"] = "h5netcdf"

    # Build granule_index → [point_indices] for all matched granules
    granule_to_points: dict[int, list[object]] = {}
    zero_match_pt_indices: list[object] = []

    for pt_idx, g_indices in plan.point_granule_map.items():
        if not g_indices:
            zero_match_pt_indices.append(pt_idx)
        else:
            for g_idx in g_indices:
                granule_to_points.setdefault(g_idx, []).append(pt_idx)

    output_rows: list[dict] = []

    # Zero-match points → single NaN row each
    for pt_idx in zero_match_pt_indices:
        row: dict = plan.points.loc[pt_idx].to_dict()
        row["granule_id"] = float("nan")
        for var in variables:
            row[var] = float("nan")
        output_rows.append(row)

    # Process granules, opening each file once.
    # Each granule is processed in its own subfunction so that xarray dataset
    # memory is released when the subfunction returns, preventing accumulation.
    for g_idx, pt_indices in sorted(granule_to_points.items()):
        gm = plan.granules[g_idx]
        file_obj = opened_files[gm.result_index]
        rows = _process_single_granule(
            file_obj, pt_indices, gm, variables, plan.points, kwargs
        )
        output_rows.extend(rows)

    if not output_rows:
        empty = plan.points.iloc[:0].copy()
        empty["granule_id"] = pd.Series(dtype=object)
        for var in variables:
            empty[var] = pd.Series(dtype=float)
        return empty

    df = pd.DataFrame(output_rows)

    # Drop bare placeholder columns for any variable that was expanded into
    # per-coordinate columns (e.g. Rrs → Rrs_412, Rrs_443, …).
    for var in variables:
        expanded = [c for c in df.columns if c.startswith(f"{var}_")]
        if expanded and var in df.columns:
            df = df.drop(columns=[var])

    return df


def _process_single_granule(
    file_obj: Any,
    pt_indices: list[Any],
    gm: "GranuleMeta",
    variables: list[str],
    points: pd.DataFrame,
    kwargs: dict[str, Any],
) -> list[dict]:
    """Open one granule and extract variables for the given point indices.

    Isolating the ``xr.open_dataset`` call in its own function allows
    Python's garbage collector to fully reclaim the xarray dataset memory
    when this function returns, preventing memory accumulation across the
    thousands of granules that a typical matchup run processes.

    Parameters
    ----------
    file_obj:
        An open file-like object (e.g., from ``earthaccess.open``).
    pt_indices:
        Row indices into *points* that fall within this granule.
    gm:
        :class:`~point_collocation.core.plan.GranuleMeta` for the granule.
    variables:
        Variable names to extract from the dataset.
    points:
        The full points DataFrame (only rows in *pt_indices* are accessed).
    kwargs:
        Keyword arguments forwarded to ``xarray.open_dataset``.

    Returns
    -------
    list[dict]
        One dict per point in *pt_indices*, ready to append to the output
        rows list.  On failure, NaN-filled dicts are returned instead.
    """
    try:
        with xr.open_dataset(file_obj, **kwargs) as ds:  # type: ignore[arg-type]
            lat_name = _find_coord(ds, _LAT_NAMES)
            lon_name = _find_coord(ds, _LON_NAMES)

            rows: list[dict] = []
            for pt_idx in pt_indices:
                row: dict = points.loc[pt_idx].to_dict()
                row["granule_id"] = gm.granule_id

                for var in variables:
                    if var not in ds or lat_name is None or lon_name is None:
                        row[var] = float("nan")
                        continue
                    try:
                        selected = ds[var].sel(
                            {lat_name: row["lat"], lon_name: row["lon"]},
                            method="nearest",
                        )
                        if selected.ndim == 0:
                            row[var] = selected.item()
                        else:
                            # Multi-dimensional: expand into coord-keyed entries
                            row[var] = float("nan")  # placeholder removed later
                            for coord_val, val in selected.to_series().items():
                                row[f"{var}_{int(coord_val)}"] = float(val)
                    except Exception:
                        row[var] = float("nan")

                rows.append(row)
            return rows

    except Exception:
        # Granule failed to open → emit NaN rows for its points
        rows = []
        for pt_idx in pt_indices:
            row = points.loc[pt_idx].to_dict()
            row["granule_id"] = gm.granule_id
            for var in variables:
                row[var] = float("nan")
            rows.append(row)
        return rows


def _find_coord(ds: xr.Dataset, candidates: tuple[str, ...]) -> str | None:
    """Return the first name in *candidates* present in *ds* coords or dims."""
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    return None
