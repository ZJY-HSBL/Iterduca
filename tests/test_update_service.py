import httpx
import pytest

from iterduca.services.update_service import UpdateService


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.github.com")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


def test_update_service_detects_newer_release(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "tag_name": "v0.9.0",
                "html_url": "https://github.com/ZJY-HSBL/Iterduca/releases/tag/v0.9.0",
            },
        ),
    )
    info = UpdateService("ZJY-HSBL/Iterduca", "0.8.0").check()

    assert info.available is True
    assert info.latest_version == "0.9.0"


def test_update_service_handles_no_release(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(404),
    )
    info = UpdateService("ZJY-HSBL/Iterduca", "0.8.0").check()

    assert info.available is False
    assert info.release_url == ""


def test_update_service_rejects_non_semver() -> None:
    with pytest.raises(ValueError):
        UpdateService._version_tuple("nightly")
