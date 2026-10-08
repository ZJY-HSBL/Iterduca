"""Capture actual Qt widgets in a clean, isolated Windows session.

These are empty-state screenshots, not mockups or live proxy data.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from iterduca.paths import AppPaths
from iterduca.ui.main_window import MainWindow
from iterduca.ui.theme import APP_STYLESHEET


def main() -> None:
    output = Path("docs/screenshots")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="iterduca-screenshots-") as temp:
        os.environ["APPDATA"] = temp
        paths = AppPaths.discover()
        paths.ensure()
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        app.setStyleSheet(APP_STYLESHEET)
        window = MainWindow(paths)
        window.resize(1280, 800)
        window.show()
        app.processEvents()
        for label in ("Overview", "Proxies", "Connections", "Settings"):
            index = next(
                index for index, button in enumerate(window.nav_buttons)
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
