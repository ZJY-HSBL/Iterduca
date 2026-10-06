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
