from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


SORT_PROFILE = "profile"
SORT_NAME = "name"
SORT_LATENCY = "latency"


@dataclass(frozen=True, slots=True)
class LatencyStatistics:
    minimum: int
    average: int
    maximum: int
    count: int


def latency_statistics(samples: Iterable[object]) -> LatencyStatistics | None:
    values: list[int] = []
    for sample in samples:
        if not isinstance(sample, Mapping):
            continue
        try:
            delay = int(sample.get("delay", -1))
        except (TypeError, ValueError):
            continue
        if delay >= 0:
            values.append(delay)

    if not values:
        return None
    return LatencyStatistics(
        minimum=min(values),
        average=round(sum(values) / len(values)),
        maximum=max(values),
        count=len(values),
    )


def arrange_proxy_names(
    names: Iterable[str],
    *,
    query: str = "",
    sort_mode: str = SORT_PROFILE,
    delays: Mapping[str, int] | None = None,
) -> list[str]:
    normalized_query = query.strip().casefold()
    items = [
        str(name)
        for name in names
        if not normalized_query or normalized_query in str(name).casefold()
    ]

    if sort_mode == SORT_PROFILE:
        return items
    if sort_mode == SORT_NAME:
        return sorted(items, key=str.casefold)
    if sort_mode == SORT_LATENCY:
        delay_map = delays or {}

        def key(name: str) -> tuple[bool, int, str]:
            value = delay_map.get(name)
            valid = isinstance(value, int) and value >= 0
            return (
                not valid,
                value if valid else 2**31 - 1,
                name.casefold(),
            )

        return sorted(items, key=key)
    raise ValueError(f"Unsupported proxy sort mode: {sort_mode}")
