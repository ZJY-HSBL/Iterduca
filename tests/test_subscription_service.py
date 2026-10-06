from pathlib import Path

import httpx
import pytest

from iterduca.services.subscription_service import SubscriptionService


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = text.encode("utf-8")

    def raise_for_status(self) -> None:
        return None


def test_add_and_update_subscription(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = [
        "proxies:\n  - {name: A, type: direct}\n",
        "proxies:\n  - {name: B, type: direct}\n",
    ]

    def fake_get(*args, **kwargs):
        return FakeResponse(payloads.pop(0))

    monkeypatch.setattr(httpx, "get", fake_get)
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")

    added = service.add("https://example.com/subscription.yaml")
    assert (tmp_path / "profiles" / added.profile_name).exists()
    assert service.list()[0].url == "https://example.com/subscription.yaml"

    updated = service.update(added.profile_name)
    text = (tmp_path / "profiles" / updated.profile_name).read_text(encoding="utf-8")
    assert "name: B" in text


def test_subscription_rejects_non_http_url(tmp_path: Path) -> None:
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")
    with pytest.raises(ValueError):
        service.add("file:///secret.yaml")


def test_update_all_refreshes_every_registered_subscription(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = iter(
        [
            "proxies:\n  - {name: A, type: direct}\n",
            "proxies:\n  - {name: B, type: direct}\n",
            "proxies:\n  - {name: A2, type: direct}\n",
            "proxies:\n  - {name: B2, type: direct}\n",
        ]
    )

    def fake_get(*args, **kwargs):
        return FakeResponse(next(payloads))

    monkeypatch.setattr(httpx, "get", fake_get)
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")
    first = service.add("https://example.com/a.yaml")
    second = service.add("https://example.com/b.yaml")

    updated = service.update_all()

    assert {item.profile_name for item in updated} == {
        first.profile_name,
        second.profile_name,
    }
    assert "name: A2" in (tmp_path / "profiles" / first.profile_name).read_text(encoding="utf-8")
    assert "name: B2" in (tmp_path / "profiles" / second.profile_name).read_text(encoding="utf-8")
