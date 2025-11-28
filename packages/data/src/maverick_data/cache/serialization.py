"""
Cache serialization utilities.

Provides efficient serialization/deserialization for cached data,
including special handling for pandas DataFrames.
"""

from __future__ import annotations

import json
import logging
import time
import zlib
from collections import defaultdict
from datetime import date, datetime
from typing import Any, cast

import msgpack
import pandas as pd

logger = logging.getLogger("maverick_data.cache.serialization")

# Serialization statistics
_serialization_stats: dict[str, float] = defaultdict(float)


def get_serialization_stats() -> dict[str, float]:
    """Get serialization statistics."""
    return dict(_serialization_stats)


def reset_serialization_stats() -> None:
    """Reset serialization statistics."""
    _serialization_stats.clear()
    _serialization_stats.update(
        {
            "serialization_time": 0.0,
            "deserialization_time": 0.0,
            "compression_savings_bytes": 0.0,
            "errors": 0.0,
        }
    )


def normalize_timezone(index: pd.Index) -> pd.DatetimeIndex:
    """Return a timezone-naive DatetimeIndex in UTC."""
    dt_index = (
        index if isinstance(index, pd.DatetimeIndex) else pd.DatetimeIndex(index)
    )

    if dt_index.tz is not None:
        dt_index = dt_index.tz_convert("UTC").tz_localize(None)

    return dt_index


def ensure_timezone_naive(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has timezone-naive datetime index."""
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = normalize_timezone(df.index)
    return df


def _json_default(value: Any) -> Any:
    """JSON serializer for unsupported types."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Series):
        return value.tolist()
    if isinstance(value, set):
        return list(value)
    raise TypeError(f"Unsupported type {type(value)!r} for cache serialization")


def _dataframe_to_payload(df: pd.DataFrame) -> dict[str, Any]:
    """Convert a DataFrame to a JSON-serializable payload."""
    normalized = ensure_timezone_naive(df)
    json_payload = cast(
        str,
        normalized.to_json(orient="split", date_format="iso", default_handler=str),
    )
    payload = json.loads(json_payload)
    payload["index_type"] = (
        "datetime" if isinstance(normalized.index, pd.DatetimeIndex) else "other"
    )
    payload["index_name"] = normalized.index.name
    return payload


def _payload_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Reconstruct a DataFrame from a serialized payload."""
    data = payload.get("data", {})
    columns = data.get("columns", [])
    frame = pd.DataFrame(data.get("data", []), columns=columns)
    index_values = data.get("index", [])

    if payload.get("index_type") == "datetime":
        index_values = pd.to_datetime(index_values)
        index = normalize_timezone(pd.DatetimeIndex(index_values))
    else:
        index = index_values

    frame.index = index
    frame.index.name = payload.get("index_name")
    return ensure_timezone_naive(frame)


def serialize_data(data: Any, key: str = "") -> bytes:
    """
    Serialize data efficiently based on type.

    Args:
        data: Data to serialize
        key: Cache key for logging

    Returns:
        Serialized bytes
    """
    start_time = time.time()

    try:
        # Handle DataFrames - use msgpack with zlib compression
        if isinstance(data, pd.DataFrame):
            df = ensure_timezone_naive(data)

            try:
                # Convert to msgpack-serializable format
                df_dict = {
                    "_type": "dataframe",
                    "data": df.to_dict("index"),
                    "index_type": (
                        "datetime"
                        if isinstance(df.index, pd.DatetimeIndex)
                        else "other"
                    ),
                    "columns": list(df.columns),
                    "index_data": [str(idx) for idx in df.index],
                }
                msgpack_data = cast(bytes, msgpack.packb(df_dict))
                compressed = zlib.compress(msgpack_data, level=1)
                return compressed
            except Exception as e:
                logger.debug(f"Msgpack DataFrame serialization failed for {key}: {e}")
                # Fall back to JSON
                json_payload = {
                    "__cache_type__": "dataframe",
                    "data": _dataframe_to_payload(df),
                }
                compressed = zlib.compress(
                    json.dumps(json_payload).encode("utf-8"), level=1
                )
                return compressed

        # Handle dictionaries with DataFrames
        if isinstance(data, dict) and any(
            isinstance(v, pd.DataFrame) for v in data.values()
        ):
            processed_data = {}
            for k, v in data.items():
                if isinstance(v, pd.DataFrame):
                    processed_data[k] = ensure_timezone_naive(v)
                else:
                    processed_data[k] = v

            try:
                serializable_data = {}
                for k, v in processed_data.items():
                    if isinstance(v, pd.DataFrame):
                        serializable_data[k] = {
                            "_type": "dataframe",
                            "data": v.to_dict("index"),
                            "index_type": (
                                "datetime"
                                if isinstance(v.index, pd.DatetimeIndex)
                                else "other"
                            ),
                        }
                    else:
                        serializable_data[k] = v

                msgpack_data = cast(bytes, msgpack.packb(serializable_data))
                return zlib.compress(msgpack_data, level=1)
            except Exception:
                payload = {
                    "__cache_type__": "dict",
                    "data": {
                        key: (
                            {
                                "__cache_type__": "dataframe",
                                "data": _dataframe_to_payload(value),
                            }
                            if isinstance(value, pd.DataFrame)
                            else value
                        )
                        for key, value in processed_data.items()
                    },
                }
                return zlib.compress(
                    json.dumps(payload, default=_json_default).encode("utf-8"),
                    level=1,
                )

        # For simple data types, try msgpack first
        if isinstance(data, dict | list | str | int | float | bool | type(None)):
            try:
                return cast(bytes, msgpack.packb(data))
            except Exception:
                return json.dumps(data, default=_json_default).encode("utf-8")

        raise TypeError(f"Unsupported cache data type {type(data)!r} for key {key}")

    except TypeError as exc:
        _serialization_stats["errors"] += 1
        logger.warning(f"Unsupported data type for cache key {key}: {exc}")
        raise
    except Exception as e:
        _serialization_stats["errors"] += 1
        logger.warning(f"Failed to serialize data for key {key}: {e}")
        try:
            return json.dumps(str(data)).encode("utf-8")
        except Exception:
            return b"null"
    finally:
        _serialization_stats["serialization_time"] += time.time() - start_time


def deserialize_data(data: bytes, key: str = "") -> Any:
    """
    Deserialize cached data with multiple format support.

    Args:
        data: Serialized bytes
        key: Cache key for logging

    Returns:
        Deserialized data
    """
    start_time = time.time()

    try:
        # Try zlib compressed data first
        if data[:2] == b"\x78\x9c":  # zlib magic bytes
            try:
                decompressed = zlib.decompress(data)
                # Try msgpack
                try:
                    result = msgpack.loads(decompressed, raw=False)
                    if isinstance(result, dict) and result.get("_type") == "dataframe":
                        df = pd.DataFrame.from_dict(result["data"], orient="index")
                        if result.get("index_data"):
                            if result.get("index_type") == "datetime":
                                df.index = pd.to_datetime(result["index_data"])
                                df.index = normalize_timezone(df.index)
                            else:
                                df.index = result["index_data"]
                        elif result.get("index_type") == "datetime":
                            df.index = pd.to_datetime(df.index)
                            df.index = normalize_timezone(df.index)
                        if result.get("columns"):
                            df = df[result["columns"]]
                        return df
                    return result
                except Exception as e:
                    logger.debug(f"Msgpack decompressed failed for {key}: {e}")
                    try:
                        return _decode_json_payload(decompressed.decode("utf-8"))
                    except Exception:
                        pass
            except Exception:
                pass

        # Try msgpack uncompressed
        try:
            result = msgpack.loads(data, raw=False)
            if isinstance(result, dict) and result.get("_type") == "dataframe":
                df = pd.DataFrame.from_dict(result["data"], orient="index")
                if result.get("index_data"):
                    if result.get("index_type") == "datetime":
                        df.index = pd.to_datetime(result["index_data"])
                        df.index = normalize_timezone(df.index)
                    else:
                        df.index = result["index_data"]
                elif result.get("index_type") == "datetime":
                    df.index = pd.to_datetime(df.index)
                    df.index = normalize_timezone(df.index)
                if result.get("columns"):
                    df = df[result["columns"]]
                return df
            return result
        except Exception:
            pass

        # Fall back to JSON
        try:
            decoded = data.decode() if isinstance(data, bytes) else data
            return _decode_json_payload(decoded)
        except Exception:
            pass

    except Exception as e:
        _serialization_stats["errors"] += 1
        logger.warning(f"Failed to deserialize cache data for key {key}: {e}")
        return None
    finally:
        _serialization_stats["deserialization_time"] += time.time() - start_time

    _serialization_stats["errors"] += 1
    logger.warning(f"Failed to deserialize cache data for key {key} - no format worked")
    return None


def _decode_json_payload(raw_data: str) -> Any:
    """Decode JSON payloads with DataFrame support."""
    payload = json.loads(raw_data)
    if isinstance(payload, dict) and payload.get("__cache_type__") == "dataframe":
        return _payload_to_dataframe(payload)
    if isinstance(payload, dict) and payload.get("__cache_type__") == "dict":
        result: dict[str, Any] = {}
        for key, value in payload.get("data", {}).items():
            if isinstance(value, dict) and value.get("__cache_type__") == "dataframe":
                result[key] = _payload_to_dataframe(value)
            else:
                result[key] = value
        return result
    return payload
