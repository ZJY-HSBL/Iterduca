from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from iterduca.constants import (
    DEFAULT_CONTROLLER_HOST,
    DEFAULT_CONTROLLER_PORT,
    DEFAULT_MIXED_PORT,
    DEFAULT_MODE,
)


@dataclass(slots=True)
class AppSettings:
    core_path: str = ""
    active_profile: str = ""
    mixed_port: int = DEFAULT_MIXED_PORT
    controller_host: str = DEFAULT_CONTROLLER_HOST
    controller_port: int = DEFAULT_CONTROLLER_PORT
    mode: str = DEFAULT_MODE
    system_proxy_enabled: bool = False
    tun_enabled: bool = False
    tun_stack: str = "mips"
    tun_auto_route: bool = True
    tun_auto_detect_interface: bool = True
    tun_dns_hijack: bool = True
    tun_strict_route: bool = False
    minimize_to_tray: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        defaults = cls()
        values = {
            key: data.get(key, getattr(defaults, key))
            for key in asdict(defaults)
        }
        values["mixed_port"] = int(values["mixed_port"])
        values["controller_port"] = int(values["controller_port"])
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def core_file(self) -> Path | None:
        return Path(self.core_path).expanduser() if self.core_path else None
