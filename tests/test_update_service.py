import hashlib
from pathlib import Path

import httpx
import pytest

from iterduca.services.update_service import UpdateInfo, UpdateService


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict | None = None,
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.github.com")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class FakeStreamResponse:
    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://github.com")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def iter_bytes(self, chunk_size: int = 65536):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]


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


def test_update_service_selects_exact_setup_and_checksum_assets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "tag_name": "v1.5.0",
                "html_url": "https://github.com/ZJY-HSBL/Iterduca/releases/tag/v1.5.0",
                "assets": [
                    {
                        "name": "Iterduca-v1.5.0-windows-x64.exe",
                        "browser_download_url": (
                            "https://github.com/ZJY-HSBL/Iterduca/releases/download/"
                            "v1.5.0/Iterduca-v1.5.0-windows-x64.exe"
                        ),
                    },
                    {
                        "name": "Iterduca-v1.5.0-windows-x64-setup.exe",
                        "browser_download_url": (
                            "https://github.com/ZJY-HSBL/Iterduca/releases/download/"
                            "v1.5.0/Iterduca-v1.5.0-windows-x64-setup.exe"
                        ),
                    },
                    {
                        "name": "SHA256SUMS.txt",
                        "browser_download_url": (
                            "https://github.com/ZJY-HSBL/Iterduca/releases/download/"
                            "v1.5.0/SHA256SUMS.txt"
                        ),
                    },
                ],
            },
        ),
    )

    info = UpdateService("ZJY-HSBL/Iterduca", "1.4.0").check()

    assert info.available is True
    assert info.installer_name == "Iterduca-v1.5.0-windows-x64-setup.exe"
    assert info.installer_url.endswith(info.installer_name)
    assert info.checksums_url.endswith("SHA256SUMS.txt")


def test_update_service_rejects_untrusted_asset_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "tag_name": "v1.5.0",
                "html_url": "https://github.com/ZJY-HSBL/Iterduca/releases/tag/v1.5.0",
                "assets": [
                    {
                        "name": "Iterduca-v1.5.0-windows-x64-setup.exe",
                        "browser_download_url": "https://example.com/setup.exe",
                    },
                    {
                        "name": "SHA256SUMS.txt",
                        "browser_download_url": "http://github.com/checksums.txt",
                    },
                ],
            },
        ),
    )

    info = UpdateService("ZJY-HSBL/Iterduca", "1.4.0").check()

    assert info.available is True
    assert info.installer_url == ""
    assert info.checksums_url == ""


def test_verified_installer_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    installer = b"verified-iterduca-setup"
    digest = hashlib.sha256(installer).hexdigest()
    filename = "Iterduca-v1.5.0-windows-x64-setup.exe"
    info = UpdateInfo(
        current_version="1.4.0",
        latest_version="1.5.0",
        available=True,
        release_url="https://github.com/ZJY-HSBL/Iterduca/releases/tag/v1.5.0",
        installer_name=filename,
        installer_url=f"https://github.com/releases/{filename}",
        checksums_url="https://github.com/releases/SHA256SUMS.txt",
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            content=f"{digest}  {filename}\n".encode(),
        ),
    )
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeStreamResponse(installer),
    )

    path = UpdateService("ZJY-HSBL/Iterduca", "1.4.0").download_verified_installer(
        info,
        tmp_path,
    )

    assert path.name == filename
    assert path.read_bytes() == installer
    assert not path.with_suffix(path.suffix + ".part").exists()


def test_hash_mismatch_rejects_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filename = "Iterduca-v1.5.0-windows-x64-setup.exe"
    info = UpdateInfo(
        current_version="1.4.0",
        latest_version="1.5.0",
        available=True,
        release_url="",
        installer_name=filename,
        installer_url=f"https://github.com/releases/{filename}",
        checksums_url="https://github.com/releases/SHA256SUMS.txt",
    )
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            content=(("0" * 64) + f"  {filename}\n").encode(),
        ),
    )
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeStreamResponse(b"tampered"),
    )

    with pytest.raises(ValueError, match="SHA-256 verification failed"):
        UpdateService("ZJY-HSBL/Iterduca", "1.4.0").download_verified_installer(
            info,
            tmp_path,
        )

    assert not (tmp_path / filename).exists()
    assert not (tmp_path / f"{filename}.part").exists()


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
