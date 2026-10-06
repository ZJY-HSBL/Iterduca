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
    startup_enabled: bool = False
    tun_enabled: bool = False
    tun_stack: str = "mips"
    tun_auto_route: bool = True
    tun_auto_detect_interface: bool = True
    tun_dns_hijack: bool = True
    tun_strict_route: bool = False
    tun_bypass_private_networks: bool = True
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

    def tun_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "enable": self.tun_enabled,
            "stack": self.tun_stack,
            "auto-route": self.tun_auto_route,
            "auto-detect-interface": self.tun_auto_detect_interface,
            "dns-hijack": ["any:53", "tcp://any:53"] if self.tun_dns_hijack else [],
            "strict-route": self.tun_strict_route,
        }
        if self.tun_bypass_private_networks:
            config["route-exclude-address"] = [
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "127.0.0.0/8",
                "169.254.0.0/16",
                "::1/128",
                "fc00::/7",
                "fe80::/10",
            ]
        return config

    @property
    def core_file(self) -> Path | None:
        return Path(self.core_path).expanduser() if self.core_path else None
