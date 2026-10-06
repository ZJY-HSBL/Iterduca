from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    available: bool
    release_url: str


class UpdateService:
    def __init__(
        self,
        repository: str,
        current_version: str,
        *,
        timeout: float = 5.0,
    ) -> None:
        self.repository = repository
        self.current_version = current_version.lstrip("v")
        self.timeout = timeout

    def check(self) -> UpdateInfo:
        response = httpx.get(
            f"https://api.github.com/repos/{self.repository}/releases/latest",
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"Iterduca/{self.current_version}",
            },
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
        url = str(payload.get("html_url", ""))
        if not latest:
            raise ValueError("Latest GitHub release does not contain a tag name")
        return UpdateInfo(
            current_version=self.current_version,
            latest_version=latest,
            available=self._version_tuple(latest) > self._version_tuple(self.current_version),
            release_url=url,
        )

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        core = value.split("-", 1)[0].split("+", 1)[0]
        parts = core.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Unsupported release version: {value}")
        return tuple(int(part) for part in parts)  # type: ignore[return-value]
