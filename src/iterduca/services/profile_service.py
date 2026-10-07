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
    group_count: int
    rule_count: int
    proxy_provider_count: int
    rule_provider_count: int
    size_bytes: int


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
        groups = data.get("proxy-groups", [])
        rules = data.get("rules", [])
        proxy_providers = data.get("proxy-providers", {})
        rule_providers = data.get("rule-providers", {})
        return ProfileInfo(
            name=path.name,
            path=path,
            proxy_count=len(proxies) if isinstance(proxies, list) else 0,
            group_count=len(groups) if isinstance(groups, list) else 0,
            rule_count=len(rules) if isinstance(rules, list) else 0,
            proxy_provider_count=(
                len(proxy_providers) if isinstance(proxy_providers, dict) else 0
            ),
            rule_provider_count=(
                len(rule_providers) if isinstance(rule_providers, dict) else 0
            ),
            size_bytes=path.stat().st_size,
        )
