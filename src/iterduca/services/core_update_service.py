from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from iterduca.constants import APP_VERSION


ProgressCallback = Callable[[int], None]


@dataclass(frozen=True, slots=True)
class CoreRelease:
    version: str
    tag: str
    asset_name: str
    download_url: str
    sha256: str
    size: int


class CoreUpdateService:
    API_URL = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
    MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
    MAX_BINARY_BYTES = 200 * 1024 * 1024

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.managed_core = directory / "mihomo.exe"
        self.metadata_file = directory / "release.json"

    def latest_windows_amd64(self) -> CoreRelease:
        response = httpx.get(
            self.API_URL,
            follow_redirects=True,
            timeout=10.0,
            headers=self._headers(),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Mihomo latest release response is invalid")

        tag = str(payload.get("tag_name", "")).strip()
        version = tag.removeprefix("v")
        if not self._version_tuple(version):
            raise ValueError("Mihomo latest release has an invalid version tag")

        expected = f"mihomo-windows-amd64-v{version}.zip"
        assets = payload.get("assets", [])
        if not isinstance(assets, list):
            raise ValueError("Mihomo release assets are missing")

        asset = next(
            (
                item
                for item in assets
                if isinstance(item, dict) and item.get("name") == expected
            ),
            None,
        )
        if asset is None:
            raise ValueError(f"Required Mihomo release asset is missing: {expected}")

        digest = str(asset.get("digest", ""))
        if not digest.startswith("sha256:"):
            raise ValueError("Mihomo release asset does not provide a SHA-256 digest")
        sha256 = digest.removeprefix("sha256:").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError("Mihomo release asset SHA-256 digest is invalid")

        url = str(asset.get("browser_download_url", ""))
        size = int(asset.get("size", 0) or 0)
        if not url.startswith("https://github.com/"):
            raise ValueError("Mihomo release asset download URL is invalid")
        if size <= 0 or size > self.MAX_ARCHIVE_BYTES:
            raise ValueError("Mihomo release asset size is outside the allowed range")

        return CoreRelease(
            version=version,
            tag=tag,
            asset_name=expected,
            download_url=url,
            sha256=sha256,
            size=size,
        )

    def install(
        self,
        release: CoreRelease,
        progress: ProgressCallback | None = None,
    ) -> Path:
        archive_path = self.directory / ".mihomo-download.zip"
        temporary_core = self.directory / ".mihomo.exe.tmp"
        hasher = hashlib.sha256()
        received = 0

        try:
            with httpx.stream(
                "GET",
                release.download_url,
                follow_redirects=True,
                timeout=60.0,
                headers=self._headers(),
            ) as response:
                response.raise_for_status()
                with archive_path.open("wb") as target:
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue
                        received += len(chunk)
                        if received > self.MAX_ARCHIVE_BYTES:
                            raise ValueError("Mihomo download exceeds the allowed size")
                        hasher.update(chunk)
                        target.write(chunk)
                        if progress and release.size > 0:
                            progress(min(100, int(received * 100 / release.size)))

            if release.size > 0 and received != release.size:
                raise ValueError(
                    f"Mihomo download size mismatch: expected {release.size}, got {received}"
                )
            if hasher.hexdigest().lower() != release.sha256.lower():
                raise ValueError("Mihomo download SHA-256 verification failed")

            with zipfile.ZipFile(archive_path, "r") as archive:
                candidates = [
                    info
                    for info in archive.infolist()
                    if (
                        not info.is_dir()
                        and Path(info.filename).name.lower().startswith("mihomo")
                        and Path(info.filename).suffix.lower() == ".exe"
                    )
                ]
                if len(candidates) != 1:
                    raise ValueError(
                        "Mihomo archive must contain exactly one executable"
                    )
                member = candidates[0]
                if member.file_size <= 0 or member.file_size > self.MAX_BINARY_BYTES:
                    raise ValueError("Mihomo executable size is outside the allowed range")
                binary = archive.read(member)

            temporary_core.write_bytes(binary)
            temporary_core.replace(self.managed_core)
            self._write_metadata(release)
            if progress:
                progress(100)
            return self.managed_core
        finally:
            for path in (archive_path, temporary_core):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    def installed_release(self) -> CoreRelease | None:
        if not self.metadata_file.exists() or not self.managed_core.exists():
            return None
        try:
            payload = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            return CoreRelease(
                version=str(payload["version"]),
                tag=str(payload["tag"]),
                asset_name=str(payload["asset_name"]),
                download_url=str(payload["download_url"]),
                sha256=str(payload["sha256"]),
                size=int(payload["size"]),
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @classmethod
    def is_newer_than_output(cls, release: CoreRelease, version_output: str) -> bool:
        current = cls.parse_version_output(version_output)
        if current is None:
            return True
        return cls._version_tuple(release.version) > cls._version_tuple(current)

    @staticmethod
    def parse_version_output(output: str) -> str | None:
        match = re.search(r"\bv(\d+\.\d+\.\d+)\b", output)
        return match.group(1) if match else None

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int] | tuple[()]:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            return ()
        return tuple(int(part) for part in parts)  # type: ignore[return-value]

    def _write_metadata(self, release: CoreRelease) -> None:
        temporary = self.metadata_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(release), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.metadata_file)

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Iterduca/{APP_VERSION}",
        }
