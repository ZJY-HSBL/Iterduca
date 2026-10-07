from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from iterduca.constants import APP_NAME


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    profiles: Path
    runtime: Path
    logs: Path
    settings_file: Path
    subscriptions_file: Path
    override_file: Path
    proxy_state_file: Path
    metrics_file: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        root = base / APP_NAME
        return cls(
            root=root,
            profiles=root / "profiles",
            runtime=root / "runtime",
            logs=root / "logs",
            settings_file=root / "settings.json",
            subscriptions_file=root / "subscriptions.json",
            override_file=root / "override.yaml",
            proxy_state_file=root / "proxy-state.json",
            metrics_file=root / "metrics.json",
        )

    def ensure(self) -> None:
        for directory in (self.root, self.profiles, self.runtime, self.logs):
            directory.mkdir(parents=True, exist_ok=True)
