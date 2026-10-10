from pathlib import Path

import httpx
import pytest

from iterduca.services.subscription_service import SubscriptionService


class FakeResponse:
    def __init__(self, text: str, headers: dict[str, str] | None = None) -> None:
        self.content = text.encode("utf-8")
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def iter_bytes(self, chunk_size: int = 65536):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset : offset + chunk_size]


def test_add_and_update_subscription(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = [
        "proxies:\n  - {name: A, type: direct}\n",
        "proxies:\n  - {name: B, type: direct}\n",
    ]

    def fake_stream(*args, **kwargs):
        return FakeResponse(payloads.pop(0))

    monkeypatch.setattr(httpx, "stream", fake_stream)
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

    def fake_stream(*args, **kwargs):
        return FakeResponse(next(payloads))

    monkeypatch.setattr(httpx, "stream", fake_stream)
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


def test_forget_subscription_removes_only_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeResponse("proxies:\n  - {name: A, type: direct}\n"),
    )
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")
    info = service.add("https://example.com/a.yaml")
    profile = tmp_path / "profiles" / info.profile_name

    service.forget(info.profile_name)

    assert service.list() == []
    assert profile.exists()


def test_subscription_userinfo_is_parsed_and_persisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeResponse(
            "proxies:\n  - {name: A, type: direct}\n",
            {
                "subscription-userinfo": (
                    "upload=1073741824; download=2147483648; "
                    "total=10737418240; expire=1893456000"
                )
            },
        ),
    )
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")

    added = service.add("https://example.com/quota.yaml")
    restored = service.list()[0]

    assert added.upload_bytes == 1073741824
    assert added.download_bytes == 2147483648
    assert added.used_bytes == 3221225472
    assert added.total_bytes == 10737418240
    assert added.remaining_bytes == 7516192768
    assert added.expire_at == 1893456000
    assert restored == added


def test_subscription_userinfo_ignores_invalid_values() -> None:
    parsed = SubscriptionService._parse_userinfo(
        "upload=bad; download=42; total=-1; expire=not-a-date; other=5"
    )

    assert parsed == {
        "upload_bytes": 0,
        "download_bytes": 42,
        "total_bytes": 0,
        "expire_at": 0,
    }


def test_malformed_persisted_subscription_usage_falls_back_to_zero(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    metadata = tmp_path / "subscriptions.json"
    metadata.write_text(
        '{"profile.yaml": {'
        '"url": "https://example.com/sub", '
        '"updated_at": "2026-10-07T00:00:00+00:00", '
        '"upload_bytes": "bad", '
        '"download_bytes": null, '
        '"total_bytes": -99, '
        '"expire_at": "invalid"}}',
        encoding="utf-8",
    )

    info = SubscriptionService(profiles, metadata).list()[0]

    assert info.upload_bytes == 0
    assert info.download_bytes == 0
    assert info.total_bytes == 0
    assert info.expire_at == 0


class OversizedStreamingResponse(FakeResponse):
    def __init__(self) -> None:
        super().__init__("proxies: []\\n")
        self.read_chunks = 0

    def iter_bytes(self, chunk_size: int = 65536):
        for _ in range(200):
            self.read_chunks += 1
            yield b"x" * chunk_size


def test_subscription_stream_stops_as_soon_as_size_limit_is_exceeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = OversizedStreamingResponse()
    monkeypatch.setattr(httpx, "stream", lambda *args, **kwargs: response)
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")

    with pytest.raises(ValueError, match="larger than 8 MiB"):
        service.add("https://example.com/oversized.yaml")

    assert response.read_chunks == 129  # 128 chunks are exactly 8 MiB
    assert list((tmp_path / "profiles").iterdir()) == []
    assert service.list() == []


def test_oversized_content_length_rejected_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class DeclaredOversizedResponse(FakeResponse):
        def iter_bytes(self, chunk_size: int = 65536):
            raise AssertionError("Body should not be read when Content-Length exceeds limit")
            yield b""  # pragma: no cover

    response = DeclaredOversizedResponse(
        "proxies: []\\n", {"content-length": str(8 * 1024 * 1024 + 1)}
    )
    monkeypatch.setattr(httpx, "stream", lambda *args, **kwargs: response)
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")
    with pytest.raises(ValueError, match="larger than 8 MiB"):
        service.add("https://example.com/oversized.yaml")


def test_failed_streamed_update_preserves_previous_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter([FakeResponse("proxies:\\n  - {name: A, type: direct}\\n"), OversizedStreamingResponse()])
    monkeypatch.setattr(httpx, "stream", lambda *args, **kwargs: next(responses))
    service = SubscriptionService(tmp_path / "profiles", tmp_path / "subscriptions.json")
    info = service.add("https://example.com/stable.yaml")
    original = (tmp_path / "profiles" / info.profile_name).read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="larger than 8 MiB"):
        service.update(info.profile_name)

    assert (tmp_path / "profiles" / info.profile_name).read_text(encoding="utf-8") == original
    assert service.list()[0] == info
