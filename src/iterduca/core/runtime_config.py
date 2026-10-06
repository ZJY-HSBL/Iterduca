from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path

import yaml

from iterduca.services.override_service import deep_merge


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    path: Path
    secret: str


class RuntimeConfigBuilder:
    """Build a disposable Mihomo config without mutating the imported profile."""

    def __init__(self, runtime_directory: Path) -> None:
        self.runtime_directory = runtime_directory
        self.runtime_directory.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        source: Path,
        *,
        mixed_port: int,
        controller_host: str,
        controller_port: int,
        mode: str,
        secret: str | None = None,
        overrides: dict | None = None,
        tun: dict | None = None,
    ) -> RuntimeConfig:
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Profile root must be a YAML mapping")

        if overrides:
            data = deep_merge(data, overrides)

        if tun is not None:
            existing_tun = data.get("tun", {})
            if not isinstance(existing_tun, dict):
                existing_tun = {}
            data["tun"] = deep_merge(existing_tun, tun)

        token = secret or secrets.token_urlsafe(24)
        data["mixed-port"] = int(mixed_port)
        data["external-controller"] = f"{controller_host}:{int(controller_port)}"
        data["secret"] = token
        data["mode"] = mode.lower()
        data.setdefault("allow-lan", False)

        target = self.runtime_directory / "config.yaml"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(target)
        return RuntimeConfig(path=target, secret=token)
