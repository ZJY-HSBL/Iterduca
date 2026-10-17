"""Ordered navigation catalog and small pure search helper."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence


NAVIGATION_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("CORE", ("Overview", "Proxies", "Proxy Providers", "Profiles")),
    ("INSPECT", ("Connections", "Rules", "Rule Providers")),
    ("SYSTEM", ("Overrides", "TUN", "Tools")),
    ("APP", ("Logs", "Settings")),
)


@dataclass(frozen=True, slots=True)
class NavigationItem:
    name: str
    section: str
    index: int


def navigation_items() -> list[NavigationItem]:
    return [
        NavigationItem(name=name, section=section, index=index)
        for index, (section, name) in enumerate(
            (section, name)
            for section, names in NAVIGATION_SECTIONS
            for name in names
        )
    ]


def search_navigation(
    items: Sequence[NavigationItem], query: str
) -> list[NavigationItem]:
    """Case-insensitive, order-preserving AND match over page and group."""
    tokens = query.casefold().split()
    if not tokens:
        return list(items)
    return [
        item
        for item in items
        if all(
            token in f"{item.name} {item.section}".casefold()
            for token in tokens
        )
    ]
