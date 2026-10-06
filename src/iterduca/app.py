from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from iterduca.paths import AppPaths
from iterduca.system.single_instance import SingleInstance
from iterduca.ui.main_window import MainWindow
from iterduca.ui.theme import APP_STYLESHEET


def main() -> int:
    background = "--background" in sys.argv
    qt_argv = [arg for arg in sys.argv if arg != "--background"]

    paths = AppPaths.discover()
    paths.ensure()

    app = QApplication(qt_argv)
    app.setApplicationName("Iterduca")
    app.setOrganizationName("ZJY-HSBL")
    app.setStyleSheet(APP_STYLESHEET)

    single_instance = SingleInstance("Iterduca-ZJY-HSBL")
    if not single_instance.primary:
        return 0

    window = MainWindow(paths)
    single_instance.activated.connect(window._show_from_tray)

    if not background or not QSystemTrayIcon.isSystemTrayAvailable():
        window.show()

    return app.exec()
