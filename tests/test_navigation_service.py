from iterduca.services.navigation_service import (
    NAVIGATION_SECTIONS,
    navigation_items,
    search_navigation,
)


def test_all_sections_and_pages_have_stable_indices():
    items = navigation_items()
    assert len(items) == 12
    assert [item.index for item in items] == list(range(12))
    assert items[0].name == "Overview"
    assert items[-1].name == "Settings"
    assert sum(len(names) for _, names in NAVIGATION_SECTIONS) == len(items)


def test_navigation_search_is_case_insensitive_and_whitespace_tolerant():
    items = navigation_items()
    assert [item.name for item in search_navigation(items, "  PROXY  ")] == [
        "Proxy Providers",
    ]
    assert [item.name for item in search_navigation(items, "inspect rules")] == [
        "Rules", "Rule Providers",
    ]
    assert [item.name for item in search_navigation(items, "core prov")] == [
        "Proxy Providers",
    ]


def test_navigation_search_keeps_sidebar_order():
    items = navigation_items()
    assert search_navigation(items, "") == items
    assert [item.name for item in search_navigation(items, "provider")] == [
        "Proxy Providers", "Rule Providers",
    ]
    assert search_navigation(items, "no such page") == []
