from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class ProfileInfo:
    name: str
    path: Path
    proxy_count: int


class ProfileService:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def import_file(self, source: Path) -> ProfileInfo:
        source = source.expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        data = self._read_yaml(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:8]
        safe_stem = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in source.stem)
        destination = self.directory / f"{safe_stem}-{digest}.yaml"
        shutil.copy2(source, destination)
        return self._info(destination, data)

    def list_profiles(self) -> list[ProfileInfo]:
        profiles: list[ProfileInfo] = []
        for path in sorted(self.directory.glob("*.y*ml")):
            try:
                data = self._read_yaml(path)
            except (OSError, ValueError, yaml.YAMLError):
                continue
            profiles.append(self._info(path, data))
        return profiles

    def resolve(self, filename: str) -> Path:
        candidate = (self.directory / filename).resolve()
        base = self.directory.resolve()
        if candidate.parent != base or not candidate.is_file():
            raise FileNotFoundError(filename)
        return candidate

    def delete(self, filename: str) -> None:
        self.resolve(filename).unlink()

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Profile root must be a YAML mapping")
        return data

    @staticmethod
    def _info(path: Path, data: dict) -> ProfileInfo:
        proxies = data.get("proxies", [])
        return ProfileInfo(
            name=path.name,
            path=path,
            proxy_count=len(proxies) if isinstance(proxies, list) else 0,
        )
