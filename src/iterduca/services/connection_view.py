from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConnectionSummary:
    count: int
    upload: int
    download: int


def non_negative_int(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def connection_id(item: object) -> str:
    if not isinstance(item, Mapping):
        return ""
    value = item.get("id")
    return str(value) if value else ""


def summarize_connections(items: Iterable[object]) -> ConnectionSummary:
    count = 0
    upload = 0
    download = 0
    for item in items:
        if not isinstance(item, Mapping):
            continue
        count += 1
        upload += non_negative_int(item.get("upload", 0))
        download += non_negative_int(item.get("download", 0))
    return ConnectionSummary(count=count, upload=upload, download=download)
