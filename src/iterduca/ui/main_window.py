from __future__ import annotations

import time
from pathlib import Path

import httpx
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from iterduca.core.api import MihomoApi
from iterduca.core.manager import CoreManager
from iterduca.core.runtime_config import RuntimeConfigBuilder
from iterduca.core.traffic import TrafficMonitor
from iterduca.paths import AppPaths
from iterduca.services.profile_service import ProfileService
from iterduca.services.settings_service import SettingsService
from iterduca.system.proxy import SystemProxy
from iterduca.ui.pages.logs import LogsPage
from iterduca.ui.pages.overview import OverviewPage
from iterduca.ui.pages.profiles import ProfilesPage
from iterduca.ui.pages.proxies import ProxiesPage
from iterduca.ui.pages.settings import SettingsPage


class UiBridge(QObject):
    log = pyqtSignal(str)
    traffic = pyqtSignal(int, int)


class MainWindow(QMainWindow):
    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.settings_service = SettingsService(paths.settings_file)
        self.profile_service = ProfileService(paths.profiles)
        self.settings = self.settings_service.load()
        self.runtime_builder = RuntimeConfigBuilder(paths.runtime)
        self.bridge = UiBridge()
        self.core = CoreManager(self.bridge.log.emit)
        self.system_proxy = SystemProxy()
        self.api: MihomoApi | None = None
        self.traffic_monitor: TrafficMonitor | None = None
        self._controller_secret = ""
        self._force_quit = False
        self._system_proxy_active = False

        self.setWindowTitle("Iterduca")
        self.resize(1080, 700)
        self.setMinimumSize(900, 580)
        self._build_ui()
        self._connect_signals()
        self._build_tray()
        self._refresh_profiles()
        self.settings_page.load_settings(self.settings)
        self.overview.set_mode(self.settings.mode)

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(190)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 16, 14, 16)
        brand = QLabel("ITERDUCA")
        brand.setObjectName("Brand")
        side.addWidget(brand)

        self.stack = QStackedWidget()
        self.overview = OverviewPage()
        self.proxies = ProxiesPage()
        self.profiles = ProfilesPage()
        self.logs = LogsPage()
        self.settings_page = SettingsPage()
        pages = [
            ("Overview", self.overview),
            ("Proxies", self.proxies),
            ("Profiles", self.profiles),
            ("Logs", self.logs),
            ("Settings", self.settings_page),
        ]
        self.nav_buttons: list[QPushButton] = []
        for index, (name, page) in enumerate(pages):
            self.stack.addWidget(page)
            button = QPushButton(name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self._navigate(i))
            self.nav_buttons.append(button)
            side.addWidget(button)
        self.nav_buttons[0].setChecked(True)
        side.addStretch(1)
        version = QLabel("v0.1.0")
        version.setObjectName("Muted")
        side.addWidget(version)

        outer.addWidget(sidebar)
        outer.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.overview.start_button.clicked.connect(self.start_core)
        self.overview.stop_button.clicked.connect(self.stop_core)
        self.overview.mode_changed.connect(self._set_mode)
        self.profiles.import_requested.connect(self._import_profile)
        self.profiles.active_profile_changed.connect(self._set_active_profile)
        self.settings_page.save_requested.connect(self._save_settings)
        self.proxies.refresh_requested.connect(self._refresh_proxies)
        self.proxies.proxy_selected.connect(self._select_proxy)
        self.bridge.log.connect(self.logs.append)
        self.bridge.traffic.connect(self.overview.set_traffic)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon)
        self.setWindowIcon(icon)
        menu = QMenu(self)
        show_action = QAction("Show Iterduca", self)
        show_action.triggered.connect(self._show_from_tray)
        start_action = QAction("Start core", self)
        start_action.triggered.connect(self.start_core)
        stop_action = QAction("Stop core", self)
        stop_action.triggered.connect(self.stop_core)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_from_tray)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(start_action)
        menu.addAction(stop_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_from_tray(self) -> None:
        self._force_quit = True
        self.stop_core()
        self.tray.hide()
        QApplication.quit()

    def _navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def start_core(self) -> None:
        if self.core.running:
            return
        try:
            executable = self.settings.core_file
            if executable is None:
                raise RuntimeError("Select the Mihomo executable in Settings first.")
            if not self.settings.active_profile:
                raise RuntimeError("Import and activate a profile first.")
            profile = self.profile_service.resolve(self.settings.active_profile)
            runtime = self.runtime_builder.build(
                profile,
                mixed_port=self.settings.mixed_port,
                controller_host="127.0.0.1",
                controller_port=self.settings.controller_port,
                mode=self.settings.mode,
            )
            self._controller_secret = runtime.secret
            self.core.start(executable, runtime.path, self.paths.runtime)
            self._wait_for_controller()
            if self.settings.system_proxy_enabled:
                self.system_proxy.enable("127.0.0.1", self.settings.mixed_port)
                self._system_proxy_active = True
            self._start_traffic()
            self._refresh_proxies()
            detail = (
                f"127.0.0.1:{self.settings.mixed_port} · "
                f"{self.settings.mode.upper()}"
            )
            self.overview.set_running(True, detail)
        except Exception as exc:
            self.core.stop()
            self.overview.set_running(False, str(exc))
            QMessageBox.critical(self, "Unable to start", str(exc))

    def stop_core(self) -> None:
        if self.traffic_monitor:
            self.traffic_monitor.stop()
            self.traffic_monitor = None
        if self.api:
            self.api.close()
            self.api = None
        if self._system_proxy_active:
            self.system_proxy.disable()
            self._system_proxy_active = False
        self.core.stop()
        self.overview.set_traffic(0, 0)
        self.overview.set_running(False)

    def _wait_for_controller(self) -> None:
        base = f"http://127.0.0.1:{self.settings.controller_port}"
        api = MihomoApi(base, self._controller_secret, timeout=0.5)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                api.version()
                self.api = api
                return
            except (httpx.HTTPError, OSError):
                time.sleep(0.1)
        api.close()
        raise RuntimeError(
            "Mihomo started but its controller did not become ready within 5 seconds."
        )

    def _start_traffic(self) -> None:
        url = f"ws://127.0.0.1:{self.settings.controller_port}/traffic"
        self.traffic_monitor = TrafficMonitor(
            url, self._controller_secret, self.bridge.traffic.emit
        )
        self.traffic_monitor.start()

    def _set_mode(self, mode: str) -> None:
        self.settings.mode = mode.lower()
        self.settings_service.save(self.settings)
        self.settings_page.load_settings(self.settings)
        if not self.api:
            return
        try:
            self.api.set_mode(self.settings.mode)
            detail = (
                f"127.0.0.1:{self.settings.mixed_port} · "
                f"{self.settings.mode.upper()}"
            )
            self.overview.set_running(True, detail)
        except Exception as exc:
            self.logs.append(f"[mode] {exc}")

    def _refresh_proxies(self) -> None:
        if not self.api:
            self.proxies.set_groups([])
            return
        try:
            self.proxies.set_groups(self.api.proxy_groups())
        except Exception as exc:
            self.logs.append(f"[api] {exc}")

    def _select_proxy(self, group: str, proxy: str) -> None:
        if not self.api:
            return
        try:
            self.api.select_proxy(group, proxy)
            self._refresh_proxies()
        except Exception as exc:
            QMessageBox.warning(self, "Proxy switch failed", str(exc))

    def _import_profile(self, path: str) -> None:
        try:
            profile = self.profile_service.import_file(Path(path))
            self.settings.active_profile = profile.name
            self.settings_service.save(self.settings)
            self._refresh_profiles()
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))

    def _set_active_profile(self, filename: str) -> None:
        self.settings.active_profile = filename
        self.settings_service.save(self.settings)
        self._refresh_profiles()

    def _refresh_profiles(self) -> None:
        self.profiles.set_profiles(
            self.profile_service.list_profiles(), self.settings.active_profile
        )

    def _save_settings(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        self.settings.core_path = str(values["core_path"])
        self.settings.mixed_port = int(values["mixed_port"])
        self.settings.controller_port = int(values["controller_port"])
        self.settings.mode = str(values["mode"])
        requested_proxy = bool(values["system_proxy_enabled"])
        if self.core.running and requested_proxy != self._system_proxy_active:
            if requested_proxy:
                self.system_proxy.enable("127.0.0.1", self.settings.mixed_port)
                self._system_proxy_active = True
            else:
                self.system_proxy.disable()
                self._system_proxy_active = False
        self.settings.system_proxy_enabled = requested_proxy
        self.settings_service.save(self.settings)
        self.overview.set_mode(self.settings.mode)
        QMessageBox.information(self, "Settings", "Settings saved.")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if (
            not self._force_quit
            and self.settings.minimize_to_tray
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            self.hide()
            event.ignore()
            return
        self.stop_core()
        event.accept()
