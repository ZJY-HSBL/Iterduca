from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import httpx
import pytest

from iterduca.services.core_update_service import CoreRelease, CoreUpdateService


class FakeJsonResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeStreamResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self) -> None:
        return None

    def iter_bytes(self):
        midpoint = max(1, len(self.content) // 2)
        yield self.content[:midpoint]
        yield self.content[midpoint:]


def make_zip(binary: bytes = b"fake-mihomo-binary") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mihomo-windows-amd64.exe", binary)
    return buffer.getvalue()


def test_latest_release_selects_generic_windows_amd64_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digest = "a" * 64
    payload = {
        "tag_name": "v1.19.32",
        "assets": [
            {
                "name": "mihomo-windows-amd64-v3-v1.19.32.zip",
                "digest": f"sha256:{'b' * 64}",
                "size": 123,
                "browser_download_url": "https://github.com/example/v3.zip",
            },
            {
                "name": "mihomo-windows-amd64-v1.19.32.zip",
                "digest": f"sha256:{digest}",
                "size": 456,
                "browser_download_url": "https://github.com/example/generic.zip",
            },
        ],
    }
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: FakeJsonResponse(payload))

    release = CoreUpdateService(tmp_path / "core").latest_windows_amd64()

    assert release.version == "1.19.32"
    assert release.asset_name == "mihomo-windows-amd64-v1.19.32.zip"
    assert release.sha256 == digest
    assert release.size == 456


def test_latest_release_requires_sha256_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "tag_name": "v1.19.32",
        "assets": [
            {
                "name": "mihomo-windows-amd64-v1.19.32.zip",
                "size": 456,
                "browser_download_url": "https://github.com/example/core.zip",
            }
        ],
    }
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: FakeJsonResponse(payload))

    with pytest.raises(ValueError, match="SHA-256"):
        CoreUpdateService(tmp_path / "core").latest_windows_amd64()


def test_install_verifies_hash_and_extracts_managed_core(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = make_zip()
    digest = hashlib.sha256(archive).hexdigest()
    release = CoreRelease(
        version="1.19.32",
        tag="v1.19.32",
        asset_name="mihomo-windows-amd64-v1.19.32.zip",
        download_url="https://github.com/example/core.zip",
        sha256=digest,
        size=len(archive),
    )
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeStreamResponse(archive),
    )
    progress: list[int] = []
    service = CoreUpdateService(tmp_path / "core")

    path = service.install(release, progress.append)

    assert path == service.managed_core
    assert path.read_bytes() == b"fake-mihomo-binary"
    assert service.installed_release() == release
    assert progress[-1] == 100


def test_install_rejects_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = make_zip()
    release = CoreRelease(
        version="1.19.32",
        tag="v1.19.32",
        asset_name="mihomo-windows-amd64-v1.19.32.zip",
        download_url="https://github.com/example/core.zip",
        sha256="0" * 64,
        size=len(archive),
    )
    monkeypatch.setattr(
        httpx,
        "stream",
        lambda *args, **kwargs: FakeStreamResponse(archive),
    )
    service = CoreUpdateService(tmp_path / "core")

    with pytest.raises(ValueError, match="SHA-256"):
        service.install(release)

    assert not service.managed_core.exists()


def test_version_output_comparison() -> None:
    release = CoreRelease(
        version="1.19.32",
        tag="v1.19.32",
        asset_name="asset.zip",
        download_url="https://github.com/example/core.zip",
        sha256="a" * 64,
        size=1,
    )

    assert CoreUpdateService.parse_version_output(
        "Mihomo Meta v1.19.31 windows amd64"
    ) == "1.19.31"
    assert CoreUpdateService.is_newer_than_output(
        release,
        "Mihomo Meta v1.19.31 windows amd64",
    ) is True
    assert CoreUpdateService.is_newer_than_output(
        release,
        "Mihomo Meta v1.19.32 windows amd64",
    ) is False
