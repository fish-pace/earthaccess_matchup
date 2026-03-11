"""Open-method specification and pipeline for point-collocation granule opening.

This module handles the "Open granule → matchup-ready xarray.Dataset" pipeline.
It is responsible for:

1. Normalizing the ``open_method`` argument (string preset → dict spec).
2. Building effective ``open_kwargs`` (applying defaults for ``chunks``,
   ``engine``, and ``decode_timedelta``).
3. Opening a file as a flat ``xarray.Dataset`` (via dataset or datatree path).
4. Normalizing coordinates (detecting lat/lon and promoting to xarray coords).

The ``open_method`` argument accepted by :func:`~point_collocation.matchup`
and related functions may be:

* A **string preset**: ``"dataset"``, ``"datatree-merge"``, or ``"auto"``.
* A **dict spec** conforming to the schema below.

Dict schema
-----------
::

    open_method = {
        "xarray_open":           "dataset" | "datatree",
        "open_kwargs":           {},
        "merge":                 "all" | "root" | ["/path/a", "/path/b"],
        "merge_kwargs":          {},
        "coords":                "auto" | ["Latitude", "Longitude"] | {"lat": "...", "lon": "..."},
        "set_coords":            True,
        "dim_renames":           None | {"node_path": {"old_dim": "new_dim"}},
        "auto_align_phony_dims": None | "safe",
    }

All keys are optional; missing keys receive sensible defaults.
Unknown keys raise a clear :exc:`ValueError` to prevent silent typos.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

import xarray as xr

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_SPEC_KEYS: frozenset[str] = frozenset(
    {
        "xarray_open",
        "open_kwargs",
        "merge",
        "merge_kwargs",
        "coords",
        "set_coords",
        "dim_renames",
        "auto_align_phony_dims",
    }
)

_VALID_XARRAY_OPEN: frozenset[str] = frozenset({"dataset", "datatree"})
_VALID_PRESETS: frozenset[str] = frozenset({"dataset", "datatree-merge", "auto"})

# Default open kwargs applied to both xr.open_dataset and xr.open_datatree
# unless explicitly overridden by the user.
_DEFAULT_OPEN_KWARGS: dict = {
    "chunks": {},
    "engine": "h5netcdf",
    "decode_timedelta": False,
}


# ---------------------------------------------------------------------------
# Open kwargs helpers
# ---------------------------------------------------------------------------


def _build_effective_open_kwargs(user_kwargs: dict) -> dict:
    """Build effective open kwargs by applying defaults to *user_kwargs*.

    Defaults applied (if not already present in *user_kwargs*):

    * ``chunks``: ``{}`` (lazy/dask loading)
    * ``engine``: ``"h5netcdf"``
    * ``decode_timedelta``: ``False``

    Parameters
    ----------
    user_kwargs:
        User-provided kwargs (e.g. from ``spec["open_kwargs"]``).

    Returns
    -------
    dict
        Effective kwargs dict with all defaults applied.
    """
    result = dict(user_kwargs)
    for key, value in _DEFAULT_OPEN_KWARGS.items():
        result.setdefault(key, value)
    return result


# ---------------------------------------------------------------------------
# Spec normalization
# ---------------------------------------------------------------------------


def _normalize_open_method(
    open_method: str | dict,
    open_dataset_kwargs: dict | None = None,
) -> dict:
    """Normalize a string preset or dict spec into a fully-specified dict.

    Parameters
    ----------
    open_method:
        Either a string preset (``"dataset"``, ``"datatree-merge"``,
        ``"auto"``) or a dict spec conforming to the open-method schema.
    open_dataset_kwargs:
        Optional top-level override for open kwargs.  These take precedence
        over any ``"open_kwargs"`` already in *open_method* (when it is a
        dict), and are applied before the shared defaults.

    Returns
    -------
    dict
        Normalized full dict spec with all required keys present.

    Raises
    ------
    TypeError
        If *open_method* is neither a str nor a dict.
    ValueError
        If a string preset is not recognised, or if a dict spec contains
        unknown keys.
    """
    if isinstance(open_method, str):
        spec = _expand_preset(open_method)
    elif isinstance(open_method, dict):
        spec = _validate_and_fill_spec(open_method)
    else:
        raise TypeError(
            f"open_method must be a string preset or dict spec, "
            f"got {type(open_method).__name__!r}."
        )

    # Merge top-level open_dataset_kwargs into spec's open_kwargs.
    # open_dataset_kwargs takes precedence over the spec's open_kwargs.
    if open_dataset_kwargs:
        merged = {**spec.get("open_kwargs", {}), **open_dataset_kwargs}
        spec = {**spec, "open_kwargs": merged}

    return spec


def _expand_preset(preset: str) -> dict:
    """Expand a string preset to a normalized dict spec.

    Parameters
    ----------
    preset:
        One of ``"dataset"``, ``"datatree-merge"``, or ``"auto"``.

    Returns
    -------
    dict
        Full dict spec.

    Raises
    ------
    ValueError
        If *preset* is not a valid string preset.
    """
    if preset == "dataset":
        return {
            "xarray_open": "dataset",
            "open_kwargs": {},
            "coords": "auto",
            "set_coords": True,
            "dim_renames": None,
            "auto_align_phony_dims": None,
        }
    if preset == "datatree-merge":
        return {
            "xarray_open": "datatree",
            "open_kwargs": {},
            "merge": "all",
            "merge_kwargs": {},
            "coords": "auto",
            "set_coords": True,
            "dim_renames": None,
            "auto_align_phony_dims": None,
        }
    if preset == "auto":
        return {
            "xarray_open": "auto",
            "open_kwargs": {},
            "coords": "auto",
            "set_coords": True,
            "dim_renames": None,
            "auto_align_phony_dims": None,
        }
    raise ValueError(
        f"open_method={preset!r} is not a valid string preset. "
        f"Must be one of {sorted(_VALID_PRESETS)} or a dict spec."
    )


def _validate_and_fill_spec(spec: dict) -> dict:
    """Validate and fill missing keys in a dict spec with sensible defaults.

    Parameters
    ----------
    spec:
        User-provided dict spec.

    Returns
    -------
    dict
        Validated and filled spec.

    Raises
    ------
    ValueError
        If *spec* contains unknown keys, or if ``"xarray_open"`` is not a
        valid value.
    """
    unknown = set(spec.keys()) - _VALID_SPEC_KEYS
    if unknown:
        raise ValueError(
            f"open_method dict contains unknown keys: {sorted(unknown)}. "
            f"Valid keys are: {sorted(_VALID_SPEC_KEYS)}."
        )

    result = dict(spec)
    result.setdefault("xarray_open", "dataset")
    result.setdefault("open_kwargs", {})
    result.setdefault("coords", "auto")
    result.setdefault("set_coords", True)
    result.setdefault("dim_renames", None)
    result.setdefault("auto_align_phony_dims", None)

    xarray_open = result["xarray_open"]
    if xarray_open not in _VALID_XARRAY_OPEN:
        raise ValueError(
            f"open_method['xarray_open']={xarray_open!r} is not valid. "
            f"Must be one of {sorted(_VALID_XARRAY_OPEN)}."
        )

    if xarray_open == "datatree":
        result.setdefault("merge", "all")
        result.setdefault("merge_kwargs", {})

    return result


# ---------------------------------------------------------------------------
# Geolocation detection
# ---------------------------------------------------------------------------

# Geolocation name pairs used as a fallback when cf_xarray is not installed or
# when the dataset lacks CF-convention attributes.
# Each element is (lon_name, lat_name), tried in order (case-sensitive).
_GEOLOC_PAIRS = [
    ("lon", "lat"),
    ("longitude", "latitude"),
    ("Longitude", "Latitude"),
    ("LONGITUDE", "LATITUDE"),
]


def _cf_geoloc_names(ds: xr.Dataset, key: str) -> list[str]:
    """Return variable names that match a CF *key* in *ds*.

    Searches both ``ds.coords`` and ``ds.data_vars`` via the ``cf_xarray``
    accessor.  Returns an empty list when ``cf_xarray`` is not installed or
    when no variables match the key.
    """
    try:
        import cf_xarray  # noqa: F401  (registers the .cf accessor)
    except ImportError:
        return []

    try:
        matched = ds.cf[[key]]
    except KeyError:
        return []

    return list(matched.coords) + list(matched.data_vars)


def _find_geoloc_pair(ds: xr.Dataset) -> tuple[str, str]:
    """Find exactly one ``(lon_name, lat_name)`` pair in *ds*.

    Detection strategy
    ------------------
    1. **cf_xarray** (primary, if installed): inspects CF-convention
       attributes such as ``standard_name``, ``units``, and ``long_name``
       in both ``ds.coords`` and ``ds.data_vars``.
    2. **Name-based fallback**: searches ``ds.coords`` and ``ds.data_vars``
       for each ``(lon_name, lat_name)`` pair in :data:`_GEOLOC_PAIRS`.

    Returns
    -------
    tuple[str, str]
        ``(lon_name, lat_name)`` of the single detected pair.

    Raises
    ------
    ValueError
        If zero pairs are found or more than one pair is found.
    """
    lon_names = _cf_geoloc_names(ds, "longitude")
    lat_names = _cf_geoloc_names(ds, "latitude")

    if lon_names or lat_names:
        if not lon_names or not lat_names:
            raise ValueError(
                "no geolocation variables found. "
                f"cf_xarray detected longitude={lon_names}, latitude={lat_names}; "
                "expected exactly one variable for each."
            )
        if len(lon_names) > 1 or len(lat_names) > 1:
            raise ValueError(
                f"ambiguous geolocation variables; "
                f"cf_xarray detected longitude={lon_names}, latitude={lat_names}. "
                "Rename or drop the extra coordinates before running matchup."
            )
        return lon_names[0], lat_names[0]

    found: list[tuple[str, str]] = []
    for lon_name, lat_name in _GEOLOC_PAIRS:
        has_lon = lon_name in ds.coords or lon_name in ds.data_vars
        has_lat = lat_name in ds.coords or lat_name in ds.data_vars
        if has_lon and has_lat:
            found.append((lon_name, lat_name))

    if len(found) == 0:
        raise ValueError(
            "no geolocation variables found. "
            "Expected one of the following (lon, lat) name pairs in ds.coords "
            f"or ds.data_vars: {_GEOLOC_PAIRS}. "
            "Specify coords explicitly via open_method={'coords': {'lat': '...', 'lon': '...'}}."
        )
    if len(found) > 1:
        raise ValueError(
            f"ambiguous geolocation variables; detected pairs: {found}. "
            "The dataset contains more than one recognised (lon, lat) pair. "
            "Rename or drop the extra coordinates before running matchup."
        )
    return found[0]


def _ensure_coords(ds: xr.Dataset, lon_name: str, lat_name: str) -> xr.Dataset:
    """Promote *lon_name* and *lat_name* to coordinates if they are data variables."""
    to_promote = [
        name
        for name in (lon_name, lat_name)
        if name in ds.data_vars and name not in ds.coords
    ]
    if to_promote:
        ds = ds.set_coords(to_promote)
    return ds


# ---------------------------------------------------------------------------
# Coordinate normalization
# ---------------------------------------------------------------------------


def _apply_coords(ds: xr.Dataset, spec: dict) -> tuple[xr.Dataset, str, str]:
    """Apply coordinate normalization from *spec* to *ds*.

    Parameters
    ----------
    ds:
        Dataset to normalize.
    spec:
        Normalized open_method dict spec.

    Returns
    -------
    tuple[xr.Dataset, str, str]
        ``(ds, lon_name, lat_name)`` where *ds* has lat/lon promoted to
        coordinates (when ``set_coords=True``).

    Raises
    ------
    ValueError
        If lat/lon cannot be identified or specified variables are absent.
    """
    coords = spec.get("coords", "auto")
    set_coords_flag = spec.get("set_coords", True)

    if coords == "auto":
        lon_name, lat_name = _find_geoloc_pair(ds)
        if set_coords_flag:
            ds = _ensure_coords(ds, lon_name, lat_name)
        return ds, lon_name, lat_name

    if isinstance(coords, list):
        missing = [n for n in coords if n not in ds and n not in ds.coords]
        if missing:
            raise ValueError(
                f"coords={coords!r}: variable(s) {missing!r} not found in dataset. "
                f"Available: {list(ds.data_vars) + list(ds.coords)}."
            )
        if set_coords_flag:
            to_promote = [n for n in coords if n in ds.data_vars and n not in ds.coords]
            if to_promote:
                ds = ds.set_coords(to_promote)
        # Auto-detect lat/lon from the (now-promoted) coords.
        lon_name, lat_name = _find_geoloc_pair(ds)
        return ds, lon_name, lat_name

    if isinstance(coords, dict):
        lat_name = coords.get("lat")
        lon_name = coords.get("lon")
        if lat_name is None or lon_name is None:
            raise ValueError(
                f"coords dict must have both 'lat' and 'lon' keys, got: {coords!r}."
            )
        for name, key in [(lat_name, "lat"), (lon_name, "lon")]:
            if name not in ds and name not in ds.coords:
                raise ValueError(
                    f"coords[{key!r}]={name!r} not found in dataset. "
                    f"Available: {list(ds.data_vars) + list(ds.coords)}."
                )
        if set_coords_flag:
            ds = _ensure_coords(ds, lon_name, lat_name)
        return ds, lon_name, lat_name

    raise ValueError(
        f"coords={coords!r} is not valid. "
        "Must be 'auto', a list of variable names, or a dict with 'lat'/'lon' keys."
    )


# ---------------------------------------------------------------------------
# DataTree helpers
# ---------------------------------------------------------------------------


def _open_datatree_fn(file_obj: object, kwargs: dict) -> object:
    """Open *file_obj* as a DataTree using whichever API is available."""
    try:
        open_dt = xr.open_datatree  # type: ignore[attr-defined]
        return open_dt(file_obj, **kwargs)  # type: ignore[arg-type]
    except AttributeError:
        pass

    try:
        import datatree  # type: ignore[import-untyped]

        return datatree.open_datatree(file_obj, **kwargs)  # type: ignore[arg-type]
    except ImportError as exc:
        raise ImportError(
            "open_method='datatree-merge' requires either xarray >= 2024.x (with "
            "built-in DataTree support) or the 'datatree' package. "
            "Install it with: pip install datatree"
        ) from exc


def _merge_datatree_with_spec(dt: object, spec: dict) -> xr.Dataset:
    """Merge DataTree nodes into a flat Dataset according to *spec*.

    Parameters
    ----------
    dt:
        An open DataTree object (``xarray.DataTree`` or ``datatree.DataTree``).
    spec:
        Normalized open_method dict spec.

    Returns
    -------
    xr.Dataset
        Merged flat dataset.
    """
    merge = spec.get("merge", "all")
    merge_kwargs: dict = spec.get("merge_kwargs", {})
    dim_renames = spec.get("dim_renames", None)
    auto_align_phony_dims = spec.get("auto_align_phony_dims", None)

    datasets: list[xr.Dataset] = []

    if merge == "root":
        root_ds = getattr(dt, "ds", None)
        if root_ds is not None and len(root_ds.data_vars) > 0:
            datasets.append(root_ds)

    elif merge == "all":
        try:
            # xarray DataTree API (>= 2024.x)
            for node in dt.subtree:  # type: ignore[union-attr]
                ds_node = node.ds
                if ds_node is not None and len(ds_node.data_vars) > 0:
                    datasets.append(ds_node)
        except AttributeError:
            # datatree package API
            for _path, node in dt.items():  # type: ignore[union-attr]
                ds_node = node.ds
                if ds_node is not None and len(ds_node.data_vars) > 0:
                    datasets.append(ds_node)

    elif isinstance(merge, list):
        for path in merge:
            try:
                node = dt[path]  # type: ignore[index]
                ds_node = node.ds
                if ds_node is not None:
                    datasets.append(ds_node)
            except (KeyError, TypeError):
                pass  # skip paths that don't exist; document: silently ignored

    else:
        raise ValueError(
            f"spec['merge']={merge!r} is not valid. "
            "Must be 'all', 'root', or a list of node paths."
        )

    # Apply dim_renames per node (before merge).
    # dim_renames maps {"node_path": {"old_dim": "new_dim", ...}}.
    # Since we don't track paths for merge="all", apply renames to each
    # dataset for all matching dim names from any path spec.
    if dim_renames and isinstance(dim_renames, dict):
        for i, ds_node in enumerate(datasets):
            rename_map: dict[str, str] = {}
            for _path, renames in dim_renames.items():
                for old_dim, new_dim in renames.items():
                    if old_dim in ds_node.dims:
                        rename_map[old_dim] = new_dim
            if rename_map:
                datasets[i] = ds_node.rename_dims(rename_map)

    if auto_align_phony_dims == "safe" and len(datasets) > 1:
        datasets = _safe_align_phony_dims(datasets)

    if not datasets:
        return xr.Dataset()

    if len(datasets) == 1:
        return datasets[0]

    effective_merge_kwargs = {"compat": "override", "join": "outer", **merge_kwargs}
    return xr.merge(datasets, **effective_merge_kwargs)


_PHONY_DIM_PATTERN = re.compile(r"^phony_dim_\d+$")


def _safe_align_phony_dims(datasets: list[xr.Dataset]) -> list[xr.Dataset]:
    """Conservative phony-dim alignment to enable merging datasets.

    Only renames when:

    * Datasets have dims matching ``phony_dim_N`` patterns.
    * The mapping is unambiguous (sizes match, at most ``len(canonical)`` dims).

    Canonical target dim names are ``("y", "x")``.

    Parameters
    ----------
    datasets:
        List of datasets to align.

    Returns
    -------
    list[xr.Dataset]
        Datasets with phony dims renamed (or unchanged if ambiguous).
    """
    canonical = ("y", "x")

    result = list(datasets)
    for i, ds in enumerate(datasets):
        phony_dims = [dim for dim in ds.dims if _PHONY_DIM_PATTERN.match(dim)]
        if not phony_dims:
            continue
        phony_sorted = sorted(phony_dims)
        if len(phony_sorted) > len(canonical):
            return datasets  # ambiguous: too many phony dims
        rename_map = {}
        for phony, canon in zip(phony_sorted, canonical):
            if canon not in ds.dims:
                rename_map[phony] = canon
        if rename_map:
            result[i] = ds.rename_dims(rename_map)

    return result


# ---------------------------------------------------------------------------
# Main context manager
# ---------------------------------------------------------------------------


@contextmanager
def _open_as_flat_dataset(
    file_obj: object,
    spec: dict,
) -> Generator[tuple[xr.Dataset, str, str], None, None]:
    """Open *file_obj* and yield ``(ds, lon_name, lat_name)``.

    The dataset *ds* has lat/lon promoted to xarray coordinates (when
    ``spec["set_coords"]`` is ``True``).

    Parameters
    ----------
    file_obj:
        File path or file-like object to open.
    spec:
        Normalized open_method dict spec (from :func:`_normalize_open_method`).

    Yields
    ------
    tuple[xr.Dataset, str, str]
        ``(ds, lon_name, lat_name)`` where *ds* is a flat dataset with
        lat/lon promoted to coordinates.
    """
    xarray_open = spec.get("xarray_open", "dataset")
    effective_kwargs = _build_effective_open_kwargs(spec.get("open_kwargs", {}))

    if xarray_open == "dataset":
        with xr.open_dataset(file_obj, **effective_kwargs) as ds:  # type: ignore[arg-type]
            ds, lon_name, lat_name = _apply_coords(ds, spec)
            yield (ds, lon_name, lat_name)

    elif xarray_open == "datatree":
        dt = _open_datatree_fn(file_obj, effective_kwargs)
        try:
            ds = _merge_datatree_with_spec(dt, spec)
            ds, lon_name, lat_name = _apply_coords(ds, spec)
            yield (ds, lon_name, lat_name)
        finally:
            if hasattr(dt, "close"):
                dt.close()

    elif xarray_open == "auto":
        yield from _open_as_flat_dataset_auto(file_obj, spec, effective_kwargs)

    else:
        raise ValueError(
            f"open_method['xarray_open']={xarray_open!r} is not valid. "
            f"Must be one of {sorted(_VALID_XARRAY_OPEN)}."
        )


def _open_as_flat_dataset_auto(
    file_obj: object,
    spec: dict,
    effective_kwargs: dict,
) -> Generator[tuple[xr.Dataset, str, str], None, None]:
    """Implement the ``"auto"`` open mode.

    Algorithm:

    1. Try ``xr.open_dataset`` (fast path).
    2. Attempt ``coords="auto"`` lat/lon discovery.
    3. If both succeed, yield the dataset.
    4. Otherwise fall back to DataTree merge (using ``merge="all"`` unless
       the user supplied an explicit ``merge`` key in the spec).
    5. If the fallback also fails to identify lat/lon, raise a combined error.
    """
    dataset_exc: BaseException | None = None
    ds_fast: xr.Dataset | None = None
    lon_name_fast: str | None = None
    lat_name_fast: str | None = None

    # --- Fast path: try xr.open_dataset ---
    try:
        ds_fast = xr.open_dataset(file_obj, **effective_kwargs)  # type: ignore[arg-type]
        ds_fast, lon_name_fast, lat_name_fast = _apply_coords(ds_fast, spec)
    except Exception as exc:
        dataset_exc = exc
        if ds_fast is not None:
            try:
                ds_fast.close()
            except Exception:
                pass
            ds_fast = None

    if ds_fast is not None:
        # Fast path succeeded.
        try:
            yield (ds_fast, lon_name_fast, lat_name_fast)  # type: ignore[misc]
        finally:
            try:
                ds_fast.close()
            except Exception:
                pass
        return

    # --- Fall back to DataTree ---
    # Attempt to seek back to start of the file object (works for seekable
    # streams; silently ignored for non-seekable objects).
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)  # type: ignore[attr-defined]
        except Exception:
            pass

    datatree_spec: dict = {
        **spec,
        "xarray_open": "datatree",
        "merge": spec.get("merge", "all"),
        "merge_kwargs": spec.get("merge_kwargs", {}),
    }

    dt = None
    try:
        try:
            dt = _open_datatree_fn(file_obj, effective_kwargs)
        except Exception as dt_open_exc:
            raise ValueError(
                "open_method='auto' failed to open granule as both a flat "
                "dataset and a DataTree.\n"
                f"  Dataset attempt: {dataset_exc!s}\n"
                f"  DataTree attempt: {dt_open_exc!s}\n"
                "Specify open_method='datatree-merge' or a dict spec to "
                "diagnose further."
            ) from dt_open_exc

        ds = _merge_datatree_with_spec(dt, datatree_spec)
        try:
            ds, lon_name, lat_name = _apply_coords(ds, datatree_spec)
        except ValueError as coord_exc:
            raise ValueError(
                "open_method='auto' could not identify lat/lon coordinates "
                "in the granule.\n"
                f"  Dataset path: {dataset_exc!s}\n"
                f"  DataTree path: {coord_exc!s}\n"
                "Fix: specify open_method with explicit coords, e.g.\n"
                "  open_method={'xarray_open': 'datatree', 'merge': 'all', "
                "'coords': {'lat': 'VariableName', 'lon': 'VariableName'}}"
            ) from coord_exc

        yield (ds, lon_name, lat_name)
    finally:
        if dt is not None and hasattr(dt, "close"):
            dt.close()
