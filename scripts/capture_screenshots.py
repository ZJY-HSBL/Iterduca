"""Capture real Iterduca Qt pages with deterministic, non-sensitive demo data.\n\nThe capture always reflects the current application version and UI branch.\n"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from iterduca.core.api import ProxyGroup
from iterduca.paths import AppPaths
from iterduca.ui.main_window import MainWindow
from iterduca.ui.theme import APP_STYLESHEET


def _populate_demo_state(window: MainWindow) -> None:
    window.overview.set_running(
        True,
        "127.0.0.1:7890 · RULE · System Proxy",
    )
    window.overview.set_mode("rule")
    window.overview.set_traffic(842_000, 4_130_000)
    window.overview.set_memory(72 * 1024 * 1024)
    window.overview.set_traffic_history(
        [
            {"up": up, "down": down}
            for up, down in (
                (180_000, 760_000),
                (260_000, 1_120_000),
                (340_000, 980_000),
                (520_000, 2_240_000),
                (430_000, 1_860_000),
                (710_000, 3_100_000),
                (640_000, 2_760_000),
                (842_000, 4_130_000),
            )
        ]
    )

    group = ProxyGroup(
        name="Auto Select",
        kind="Selector",
        now="Tokyo 01",
        all=("Tokyo 01", "Singapore 01", "Hong Kong 01", "Los Angeles 01"),
    )
    window.proxies.set_groups([group])
    for name, delay in (
        ("Tokyo 01", 38),
        ("Singapore 01", 72),
        ("Hong Kong 01", 54),
        ("Los Angeles 01", 146),
    ):
        window.proxies.set_delay("Auto Select", name, delay)
    window.proxies.set_latency_history(
        "Auto Select",
        "Tokyo 01",
        [{"delay": value} for value in (44, 41, 39, 42, 38, 40, 38)],
    )

    window.connections.set_connections(
        {
            "connections": [
                {
                    "id": "demo-1",
                    "metadata": {
                        "host": "github.com",
                        "process": "chrome.exe",
                        "network": "tcp",
                    },
                    "chains": ["Tokyo 01", "Auto Select"],
                    "rule": "DOMAIN-SUFFIX,github.com",
                    "upload": 186_240,
                    "download": 2_921_430,
                },
                {
                    "id": "demo-2",
                    "metadata": {
                        "host": "api.github.com",
                        "process": "Iterduca.exe",
                        "network": "tcp",
                    },
                    "chains": ["Tokyo 01", "Auto Select"],
                    "rule": "MATCH",
                    "upload": 32_810,
                    "download": 418_220,
                },
                {
                    "id": "demo-3",
                    "metadata": {
                        "host": "cdn.example.net",
                        "process": "code.exe",
                        "network": "tcp",
                    },
                    "chains": ["Singapore 01", "Auto Select"],
                    "rule": "DOMAIN-SUFFIX,example.net",
                    "upload": 91_570,
                    "download": 1_284_000,
                },
            ]
        }
    )

    window.settings_page.core_path.setText(
        r"C:\Users\demo\AppData\Roaming\Iterduca\core\mihomo.exe"
    )
    window.settings_page.set_core_status("Managed Mihomo Core · verified")
    window.settings_page.set_core_update_status("Latest release is installed")


def main() -> None:
    output = Path("docs/screenshots")
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="iterduca-screenshots-") as temp:
        os.environ["APPDATA"] = temp
        paths = AppPaths.discover()
        paths.ensure()

        app = QApplication([])
        app.setApplicationName("Iterduca")
        app.setOrganizationName("ZJY-HSBL")
        app.setQuitOnLastWindowClosed(False)
        app.setStyleSheet(APP_STYLESHEET)

        window = MainWindow(paths)
        window.resize(1360, 860)
        _populate_demo_state(window)
        window.show()
        app.processEvents()

        for label in ("Overview", "Proxies", "Connections", "Settings"):
            index = next(
                index
                for index, button in enumerate(window.nav_buttons)
                if button.text() == label
            )
            window._navigate(index)
            app.processEvents()
            filename = output / f"{label.lower()}.png"
            if not window.grab().save(str(filename), "PNG"):
                raise RuntimeError(f"Could not save screenshot: {filename}")
            print(f"Captured {filename}")

        window._force_quit = True
        window.close()
        app.quit()


if __name__ == "__main__":
    main()
