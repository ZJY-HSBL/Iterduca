from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from iterduca.paths import AppPaths
from iterduca.ui.main_window import MainWindow
from iterduca.ui.theme import APP_STYLESHEET


def main() -> int:
    paths = AppPaths.discover()
    paths.ensure()
    app = QApplication(sys.argv)
    app.setApplicationName("Iterduca")
    app.setOrganizationName("ZJY-HSBL")
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow(paths)
    window.show()
    return app.exec()
