from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    available: bool
    release_url: str
    installer_name: str = ""
    installer_url: str = ""
    installer_digest: str = ""
    checksums_url: str = ""


class UpdateService:
    MAX_INSTALLER_BYTES = 256 * 1024 * 1024
    MAX_CHECKSUM_BYTES = 256 * 1024

    def __init__(
        self,
        repository: str,
        current_version: str,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.repository = repository
        self.current_version = current_version.lstrip("v")
        self.timeout = timeout

    def check(self) -> UpdateInfo:
        response = httpx.get(
            f"https://api.github.com/repos/{self.repository}/releases/latest",
            timeout=self.timeout,
            follow_redirects=True,
            headers=self._headers(),
        )
        if response.status_code == 404:
            return UpdateInfo(
                current_version=self.current_version,
                latest_version=self.current_version,
                available=False,
                release_url="",
            )
        response.raise_for_status()
        payload = response.json()
        latest = str(payload.get("tag_name", "")).lstrip("v")
        release_url = str(payload.get("html_url", ""))
        if not latest:
            raise ValueError("Latest GitHub release does not contain a tag name")

        installer_name = f"Iterduca-v{latest}-windows-x64-setup.exe"
        installer_url = ""
        installer_digest = ""
        checksums_url = ""
        assets = payload.get("assets", [])
        if isinstance(assets, list):
            for item in assets:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                url = str(item.get("browser_download_url", ""))
                if name == installer_name:
                    installer_url = self._validated_download_url(url)
                    installer_digest = self._normalized_asset_digest(
                        str(item.get("digest", ""))
                    )
                elif name == "SHA256SUMS.txt":
                    checksums_url = self._validated_download_url(url)

        available = self._version_tuple(latest) > self._version_tuple(
            self.current_version
        )
        return UpdateInfo(
            current_version=self.current_version,
            latest_version=latest,
            available=available,
            release_url=release_url,
            installer_name=installer_name if installer_url else "",
            installer_url=installer_url,
            installer_digest=installer_digest,
            checksums_url=checksums_url,
        )

    def download_verified_installer(
        self,
        info: UpdateInfo,
        directory: Path,
    ) -> Path:
        if not info.available:
            raise ValueError("No newer Iterduca release is available")
        if not info.installer_name or not info.installer_url:
            raise ValueError("Latest release does not contain the Windows Setup installer")
        if not info.installer_digest:
            raise ValueError("Latest release does not provide the installer SHA-256 digest")
        if not info.checksums_url:
            raise ValueError("Latest release does not contain SHA256SUMS.txt")

        expected = self._download_checksum(
            info.checksums_url,
            info.installer_name,
        )

        if expected != info.installer_digest:
            raise ValueError(
                "GitHub Release digest does not match SHA256SUMS.txt"
            )

        directory.mkdir(parents=True, exist_ok=True)
        target = directory / info.installer_name
        temporary = target.with_suffix(target.suffix + ".part")
        hasher = hashlib.sha256()
        size = 0

        try:
            with httpx.stream(
                "GET",
                info.installer_url,
                headers=self._headers(),
                timeout=max(self.timeout, 30.0),
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                with temporary.open("wb") as handle:
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        size += len(chunk)
                        if size > self.MAX_INSTALLER_BYTES:
                            raise ValueError("Installer exceeds the 256 MiB safety limit")
                        hasher.update(chunk)
                        handle.write(chunk)

            actual = hasher.hexdigest().lower()
            if actual != expected:
                raise ValueError(
                    "Installer SHA-256 verification failed; the update was not installed"
                )
            temporary.replace(target)
            return target
        except Exception:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    def launch_installer(self, path: Path) -> None:
        executable = path.expanduser().resolve()
        if not executable.is_file():
            raise FileNotFoundError(executable)
        if os.name != "nt":
            raise OSError("Iterduca Setup installation is supported on Windows only")
        subprocess.Popen([str(executable)], close_fds=True)

    def _download_checksum(self, url: str, filename: str) -> str:
        response = httpx.get(
            url,
            headers=self._headers(),
            timeout=self.timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
        content = response.content
        if len(content) > self.MAX_CHECKSUM_BYTES:
            raise ValueError("SHA256SUMS.txt exceeds the safety limit")

        for line in content.decode("utf-8-sig", errors="strict").splitlines():
            digest, separator, name = line.strip().partition("  ")
            if not separator:
                continue
            if name.strip() != filename:
                continue
            normalized = digest.strip().lower()
            if len(normalized) != 64 or any(
                char not in "0123456789abcdef" for char in normalized
            ):
                raise ValueError("Release checksum entry is malformed")
            return normalized

        raise ValueError(f"SHA256SUMS.txt has no entry for {filename}")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Iterduca/{self.current_version}",
        }

    @staticmethod
    def _normalized_asset_digest(value: str) -> str:
        prefix = "sha256:"
        normalized = value.strip().lower()
        if not normalized.startswith(prefix):
            return ""
        digest = normalized.removeprefix(prefix)
        if len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest
        ):
            return ""
        return digest

    @staticmethod
    def _validated_download_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {
            "github.com",
            "api.github.com",
        }:
            return ""
        return url

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        core = value.split("-", 1)[0].split("+", 1)[0]
        parts = core.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Unsupported release version: {value}")
        return tuple(int(part) for part in parts)  # type: ignore[return-value]
