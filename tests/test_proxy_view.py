import pytest

from iterduca.services.proxy_view import (
    SORT_LATENCY,
    SORT_NAME,
    SORT_PROFILE,
    arrange_proxy_names,
)


def test_proxy_view_preserves_profile_order_by_default() -> None:
    names = ["Tokyo 02", "Tokyo 01", "US 01"]

    assert arrange_proxy_names(names, sort_mode=SORT_PROFILE) == names


def test_proxy_view_filters_case_insensitively_and_sorts_by_name() -> None:
    names = ["US Beta", "Tokyo 02", "tokyo 01", "HK"]

    arranged = arrange_proxy_names(
        names,
        query="TOKYO",
        sort_mode=SORT_NAME,
    )

    assert arranged == ["tokyo 01", "Tokyo 02"]


def test_proxy_view_latency_sort_places_unavailable_last() -> None:
    names = ["Slow", "Untested", "Fast", "Timeout"]
    delays = {
        "Slow": 180,
        "Fast": 32,
        "Timeout": -1,
    }

    arranged = arrange_proxy_names(
        names,
        sort_mode=SORT_LATENCY,
        delays=delays,
    )

    assert arranged == ["Fast", "Slow", "Timeout", "Untested"]


def test_proxy_view_rejects_unknown_sort_mode() -> None:
    with pytest.raises(ValueError):
        arrange_proxy_names(["A"], sort_mode="mystery")
