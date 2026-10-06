from __future__ import annotations

import json
import platform
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from iterduca.constants import APP_VERSION
from iterduca.models.settings import AppSettings
from iterduca.paths import AppPaths


class DiagnosticsService:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def export(self, destination: Path, settings: AppSettings) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        safe_settings = {
            "mixed_port": settings.mixed_port,
            "controller_host": settings.controller_host,
            "controller_port": settings.controller_port,
            "mode": settings.mode,
            "system_proxy_enabled": settings.system_proxy_enabled,
            "startup_enabled": settings.startup_enabled,
            "tun_enabled": settings.tun_enabled,
            "tun_stack": settings.tun_stack,
            "tun_auto_route": settings.tun_auto_route,
            "tun_auto_detect_interface": settings.tun_auto_detect_interface,
            "tun_dns_hijack": settings.tun_dns_hijack,
            "tun_strict_route": settings.tun_strict_route,
            "tun_bypass_private_networks": settings.tun_bypass_private_networks,
            "active_profile_set": bool(settings.active_profile),
            "core_path_set": bool(settings.core_path),
        }
        metadata = {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "iterduca_version": APP_VERSION,
            "python": sys.version,
            "platform": platform.platform(),
            "settings": safe_settings,
        }

        with zipfile.ZipFile(
            destination,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                "diagnostics.json",
                json.dumps(metadata, ensure_ascii=False, indent=2),
            )
            for log_file in sorted(self.paths.logs.glob("iterduca.log*")):
                if log_file.is_file():
                    archive.write(log_file, f"logs/{log_file.name}")
