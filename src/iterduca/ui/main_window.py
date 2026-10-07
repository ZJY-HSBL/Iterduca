from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
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

from iterduca.constants import APP_VERSION
from iterduca.core.api import MihomoApi
from iterduca.core.manager import CoreManager
from iterduca.core.runtime_config import RuntimeConfigBuilder
from iterduca.core.traffic import TrafficMonitor
from iterduca.paths import AppPaths
from iterduca.services.backup_service import BackupService
from iterduca.services.core_locator import CoreLocator
from iterduca.services.core_update_service import CoreRelease, CoreUpdateService
from iterduca.services.diagnostics_service import DiagnosticsService
from iterduca.services.history_service import HistoryService
from iterduca.services.log_service import LogService
from iterduca.services.network_service import find_port_conflicts
from iterduca.services.override_service import OverrideService
from iterduca.services.profile_service import ProfileService
from iterduca.services.restart_policy import CoreRestartPolicy
from iterduca.services.settings_service import SettingsService
from iterduca.services.subscription_service import SubscriptionService
from iterduca.services.update_service import UpdateInfo, UpdateService
from iterduca.system.privilege import is_elevated, relaunch_elevated
from iterduca.system.proxy import SystemProxy
from iterduca.system.startup import StartupService
from iterduca.ui.pages.connections import ConnectionsPage
from iterduca.ui.pages.logs import LogsPage
from iterduca.ui.pages.overrides import OverridesPage
from iterduca.ui.pages.overview import OverviewPage
from iterduca.ui.pages.profiles import ProfilesPage
from iterduca.ui.pages.proxies import ProxiesPage
from iterduca.ui.pages.proxy_providers import ProxyProvidersPage
from iterduca.ui.pages.rule_providers import RuleProvidersPage
from iterduca.ui.pages.rules import RulesPage
from iterduca.ui.pages.settings import SettingsPage
from iterduca.ui.pages.tools import ToolsPage
from iterduca.ui.pages.tun import TunPage


class UiBridge(QObject):
    log = pyqtSignal(str)
    traffic = pyqtSignal(int, int)
    latency = pyqtSignal(str, str, int)
    subscription_ready = pyqtSignal(str)
    subscription_error = pyqtSignal(str)
    memory = pyqtSignal(int)
    rule_provider_updated = pyqtSignal(str)
    rule_provider_error = pyqtSignal(str)
    proxy_provider_updated = pyqtSignal(str)
    proxy_provider_error = pyqtSignal(str)
    dns_result = pyqtSignal(object)
    dns_error = pyqtSignal(str)
    update_result = pyqtSignal(object)
    update_error = pyqtSignal(str)
    update_installer_ready = pyqtSignal(str)
    core_release_status = pyqtSignal(object)
    core_update_progress = pyqtSignal(int)
    core_update_error = pyqtSignal(str)
    core_install_done = pyqtSignal(object)


class MainWindow(QMainWindow):
    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.settings_service = SettingsService(paths.settings_file)
        self.profile_service = ProfileService(paths.profiles)
        self.subscription_service = SubscriptionService(
            paths.profiles, paths.subscriptions_file
        )
        self.override_service = OverrideService(paths.override_file)
        self.log_service = LogService(paths.logs)
        self.history_service = HistoryService(paths.metrics_file)
        self.backup_service = BackupService(paths)
        self.diagnostics_service = DiagnosticsService(paths)
        self.update_service = UpdateService("ZJY-HSBL/Iterduca", APP_VERSION)
        self.core_update_service = CoreUpdateService(paths.root / "core")
        self.settings = self.settings_service.load()
        self.core_locator = CoreLocator()
        configured_core = self.settings.core_file
        if configured_core is None or not configured_core.is_file():
            replacement_core: Path | None = None
            if self.core_update_service.managed_core.is_file():
                replacement_core = self.core_update_service.managed_core
            else:
                replacement_core = self.core_locator.discover()
            self.settings.core_path = (
                str(replacement_core) if replacement_core is not None else ""
            )
            self.settings_service.save(self.settings)
        self.startup_service = StartupService()
        if self.startup_service.supported:
            self.settings.startup_enabled = self.startup_service.is_enabled()
        self.runtime_builder = RuntimeConfigBuilder(paths.runtime)
        self.bridge = UiBridge()
        self.core = CoreManager(self.bridge.log.emit)
        self.system_proxy = SystemProxy(paths.proxy_state_file)
        self.api: MihomoApi | None = None
        self.traffic_monitor: TrafficMonitor | None = None
        self._controller_secret = ""
        self._force_quit = False
        self._system_proxy_active = False
        self._latest_traffic = (0, 0)
        self._latest_update: UpdateInfo | None = None
        self._update_download_inflight = False
        self._subscription_update_inflight = False
        self._core_update_inflight = False
        self._latest_core_release: CoreRelease | None = None
        self._restart_policy = CoreRestartPolicy(
            max_attempts=3,
            window_seconds=60,
        )
        self._restart_scheduled = False

        proxy_recovery_message = ""
        try:
            if self.system_proxy.recover_stale():
                proxy_recovery_message = (
                    "[system-proxy] Restored stale Windows proxy state from a previous crash."
                )
        except OSError as exc:
            proxy_recovery_message = f"[system-proxy] Recovery check failed: {exc}"

        self.setWindowTitle("Iterduca")
        self.resize(1080, 700)
        self.setMinimumSize(900, 580)
        self._build_ui()
        self.overview.set_traffic_history(self.history_service.traffic())
        self._restore_recent_logs()
        if proxy_recovery_message:
            self._log(proxy_recovery_message)
        self._connect_signals()
        self._build_tray()
        self._refresh_profiles()
        self.settings_page.load_settings(self.settings)
        self.overview.set_mode(self.settings.mode)
        self._load_overrides()
        self._refresh_tun_status()
        self._build_health_timer()
        self._build_subscription_timer()
        if self.settings.auto_start_core:
            QTimer.singleShot(300, self._auto_start_core)

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
        self.proxy_providers = ProxyProvidersPage()
        self.profiles = ProfilesPage()
        self.connections = ConnectionsPage()
        self.rules = RulesPage()
        self.rule_providers = RuleProvidersPage()
        self.overrides = OverridesPage()
        self.tun = TunPage()
        self.tools = ToolsPage()
        self.logs = LogsPage()
        self.settings_page = SettingsPage()
        pages = [
            ("Overview", self.overview),
            ("Proxies", self.proxies),
            ("Proxy Providers", self.proxy_providers),
            ("Profiles", self.profiles),
            ("Connections", self.connections),
            ("Rules", self.rules),
            ("Rule Providers", self.rule_providers),
            ("Overrides", self.overrides),
            ("TUN", self.tun),
            ("Tools", self.tools),
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
        version = QLabel(f"v{APP_VERSION}")
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
        self.profiles.subscription_add_requested.connect(self._add_subscription)
        self.profiles.subscription_update_requested.connect(self._update_subscription)
        self.profiles.subscription_update_all_requested.connect(
            self._update_all_subscriptions
        )
        self.profiles.delete_requested.connect(self._delete_profile)
        self.settings_page.save_requested.connect(self._save_settings)
        self.settings_page.detect_core_requested.connect(self._detect_core)
        self.settings_page.check_core_requested.connect(self._check_core_version)
        self.settings_page.check_latest_core_requested.connect(
            self._check_latest_core
        )
        self.settings_page.install_latest_core_requested.connect(
            self._install_latest_core
        )
        self.proxies.refresh_requested.connect(self._refresh_proxies)
        self.proxies.proxy_selected.connect(self._select_proxy)
        self.proxies.latency_requested.connect(self._test_latency)
        self.proxies.latency_group_requested.connect(self._test_latency_group)
        self.proxies.history_requested.connect(self._show_latency_history)
        self.proxy_providers.refresh_requested.connect(self._refresh_proxy_providers)
        self.proxy_providers.update_requested.connect(self._update_proxy_provider)
        self.proxy_providers.update_all_requested.connect(
            self._update_all_proxy_providers
        )
        self.proxy_providers.healthcheck_requested.connect(
            self._healthcheck_proxy_provider
        )
        self.connections.refresh_requested.connect(self._refresh_connections)
        self.connections.close_selected_requested.connect(self._close_connection)
        self.connections.close_all_requested.connect(self._close_all_connections)
        self.rules.refresh_requested.connect(self._refresh_rules)
        self.rules.toggle_requested.connect(self._toggle_rule)
        self.rule_providers.refresh_requested.connect(self._refresh_rule_providers)
        self.rule_providers.update_requested.connect(self._update_rule_provider)
        self.rule_providers.update_all_requested.connect(
            self._update_all_rule_providers
        )
        self.overrides.save_requested.connect(self._save_overrides)
        self.overrides.reload_requested.connect(self._load_overrides)
        self.tun.save_requested.connect(self._save_tun)
        self.tun.elevate_requested.connect(self._elevate)
        self.tun.recover_requested.connect(self._recover_standard_mode)
        self.tools.flush_dns_requested.connect(self._flush_dns_cache)
        self.tools.flush_fakeip_requested.connect(self._flush_fakeip_cache)
        self.tools.dns_query_requested.connect(self._dns_query)
        self.tools.check_update_requested.connect(self._check_for_updates)
        self.tools.install_update_requested.connect(self._install_application_update)
        self.tools.export_backup_requested.connect(self._export_backup)
        self.tools.restore_backup_requested.connect(self._restore_backup)
        self.tools.export_diagnostics_requested.connect(self._export_diagnostics)
        self.logs.export_requested.connect(self._export_logs)
        self.logs.clear_requested.connect(self._clear_logs)
        self.bridge.log.connect(self._log)
        self.bridge.traffic.connect(self._on_traffic)
        self.bridge.latency.connect(self._on_latency_result)
        self.bridge.subscription_ready.connect(self._on_subscription_ready)
        self.bridge.subscription_error.connect(self._on_subscription_error)
        self.bridge.memory.connect(self.overview.set_memory)
        self.bridge.rule_provider_updated.connect(self._on_rule_provider_updated)
        self.bridge.rule_provider_error.connect(self._on_rule_provider_error)
        self.bridge.proxy_provider_updated.connect(self._on_proxy_provider_updated)
        self.bridge.proxy_provider_error.connect(self._on_proxy_provider_error)
        self.bridge.dns_result.connect(self.tools.set_dns_result)
        self.bridge.dns_error.connect(
            lambda message: self.tools.set_dns_result(f"DNS query failed: {message}")
        )
        self.bridge.update_result.connect(self._on_update_result)
        self.bridge.update_error.connect(self._on_update_error)
        self.bridge.update_installer_ready.connect(self._on_update_installer_ready)
        self.bridge.core_release_status.connect(self._on_core_release_status)
        self.bridge.core_update_progress.connect(
            self.settings_page.set_core_update_progress
        )
        self.bridge.core_update_error.connect(self._on_core_update_error)
        self.bridge.core_install_done.connect(self._on_core_install_done)

    def _restore_recent_logs(self) -> None:
        for line in self.log_service.tail():
            self.logs.append(line)

    def _log(self, message: str) -> None:
        self.logs.append(message)
        self.log_service.append(message)

    def _export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export logs",
            "Iterduca.log",
            "Log files (*.log);;Text files (*.txt);;All files (*)",
        )
        if not path:
            return
        try:
            self.log_service.export(Path(path))
            QMessageBox.information(self, "Logs", f"Logs exported to:\n{path}")
        except OSError as exc:
            QMessageBox.warning(self, "Export logs", str(exc))

    def _clear_logs(self) -> None:
        try:
            self.log_service.clear()
        except OSError as exc:
            QMessageBox.warning(self, "Clear logs", str(exc))

    def _check_for_updates(self) -> None:
        self._latest_update = None
        self.tools.set_update_status(
            "Checking GitHub Releases…",
            install_enabled=False,
        )

        def worker() -> None:
            try:
                self.bridge.update_result.emit(self.update_service.check())
            except Exception as exc:
                self.bridge.update_error.emit(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_result(self, result: object) -> None:
        if not isinstance(result, UpdateInfo):
            return
        self._latest_update = result
        if result.available:
            if result.installer_url and result.installer_digest and result.checksums_url:
                self.tools.set_update_status(
                    f"Update available: v{result.latest_version}. "
                    "Verified Windows Setup is available.",
                    install_enabled=True,
                )
            else:
                self.tools.set_update_status(
                    f"Update available: v{result.latest_version}, but the release "
                    "does not contain both Setup and SHA256SUMS.txt.",
                    install_enabled=False,
                )
            return
        self.tools.set_update_status(
            f"No newer release found. Current v{result.current_version}; "
            f"latest published v{result.latest_version}.",
            install_enabled=False,
        )

    def _install_application_update(self) -> None:
        info = self._latest_update
        if info is None or not info.available:
            self.tools.set_update_status(
                "Check for updates before downloading.",
                install_enabled=False,
            )
            return
        if self._update_download_inflight:
            return

        answer = QMessageBox.question(
            self,
            "Install Iterduca update",
            f"Download and verify Iterduca v{info.latest_version} Setup?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._update_download_inflight = True
        self.tools.set_update_status(
            f"Downloading Iterduca v{info.latest_version}…",
            install_enabled=False,
        )

        def worker() -> None:
            try:
                path = self.update_service.download_verified_installer(
                    info,
                    self.paths.root / "updates",
                )
                self.bridge.update_installer_ready.emit(str(path))
            except Exception as exc:
                self.bridge.update_error.emit(str(exc))
            finally:
                self._update_download_inflight = False

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_installer_ready(self, path: str) -> None:
        info = self._latest_update
        version = info.latest_version if info is not None else "new"
        answer = QMessageBox.question(
            self,
            "Install verified update",
            f"Iterduca v{version} was downloaded and SHA-256 verified. "
            "Install it now? Iterduca will close.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.tools.set_update_status(
                f"Verified installer saved to: {path}",
                install_enabled=True,
            )
            return

        try:
            self.stop_core()
            self._force_quit = True
            self.tray.hide()
            self.update_service.launch_installer(Path(path))
            QApplication.quit()
        except Exception as exc:
            self.tools.set_update_status(
                f"Unable to start installer: {exc}",
                install_enabled=True,
            )
            self._log(f"[update] Unable to start installer: {exc}")

    def _on_update_error(self, message: str) -> None:
        can_retry = bool(
            self._latest_update
            and self._latest_update.available
            and self._latest_update.installer_url
            and self._latest_update.installer_digest
            and self._latest_update.checksums_url
        )
        self.tools.set_update_status(
            f"Update failed: {message}",
            install_enabled=can_retry,
        )
        self._log(f"[update] {message}")

    def _export_backup(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Iterduca backup",
            "Iterduca-backup.zip",
            "ZIP archives (*.zip)",
        )
        if not path:
            return
        try:
            self.backup_service.export(Path(path))
            QMessageBox.information(
                self,
                "Backup",
                "Backup exported. Keep it private because Profile files may contain "
                "proxy credentials.",
            )
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Backup", str(exc))

    def _restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Iterduca backup",
            "",
            "ZIP archives (*.zip)",
        )
        if not path:
            return

        answer = QMessageBox.question(
            self,
            "Restore backup",
            "Restore this backup? Current local Profiles and configuration files "
            "will be replaced.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.stop_core()
            self.backup_service.restore(Path(path))
            self.settings = self.settings_service.load()

            if self.startup_service.supported:
                self.startup_service.set_enabled(self.settings.startup_enabled)

            self.settings_page.load_settings(self.settings)
            self.overview.set_mode(self.settings.mode)
            self._refresh_profiles()
            self._load_overrides()
            self._refresh_tun_status()
            self._log("[backup] Configuration backup restored.")
            QMessageBox.information(
                self,
                "Restore backup",
                "Backup restored successfully.",
            )
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Restore backup", str(exc))

    def _export_diagnostics(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export diagnostics",
            "Iterduca-diagnostics.zip",
            "ZIP archives (*.zip)",
        )
        if not path:
            return
        try:
            self.diagnostics_service.export(Path(path), self.settings)
            QMessageBox.information(
                self,
                "Diagnostics",
                "Diagnostics exported without Profiles, subscription URLs, "
                "runtime configuration, or controller secrets.",
            )
        except OSError as exc:
            QMessageBox.warning(self, "Diagnostics", str(exc))

    def _build_health_timer(self) -> None:
        self._connection_refresh_tick = 0
        self._memory_refresh_tick = 0
        self._traffic_history_tick = 0
        self._history_flush_tick = 0
        self._memory_request_inflight = False
        self.health_timer = QTimer(self)
        self.health_timer.setInterval(1000)
        self.health_timer.timeout.connect(self._poll_core_state)
        self.health_timer.start()

    def _build_subscription_timer(self) -> None:
        self.subscription_timer = QTimer(self)
        self.subscription_timer.timeout.connect(
            lambda: self._update_all_subscriptions(background=True)
        )
        self._configure_subscription_timer()

    def _configure_subscription_timer(self) -> None:
        self.subscription_timer.stop()
        if not self.settings.subscription_auto_update_enabled:
            return
        interval_ms = (
            max(1, self.settings.subscription_update_interval_hours)
            * 60
            * 60
            * 1000
        )
        self.subscription_timer.setInterval(interval_ms)
        self.subscription_timer.start()

    def _poll_core_state(self) -> None:
        has_runtime_state = (
            self.api is not None
            or self.traffic_monitor is not None
            or self._system_proxy_active
        )
        if has_runtime_state and not self.core.running:
            should_restart = self.settings.restart_core_on_crash
            self._log("[core] Mihomo exited unexpectedly; runtime state restored.")
            self.stop_core()
            if should_restart:
                self._schedule_core_restart()
            return

        if self.api:
            self._memory_refresh_tick += 1
            self._traffic_history_tick += 1
            self._history_flush_tick += 1

            if self._memory_refresh_tick >= 2:
                self._memory_refresh_tick = 0
                self._refresh_memory()

            if self._traffic_history_tick >= 5:
                self._traffic_history_tick = 0
                up, down = self._latest_traffic
                self.history_service.record_traffic(up, down)
                self.overview.set_traffic_history(self.history_service.traffic())

            if self._history_flush_tick >= 30:
                self._history_flush_tick = 0
                self.history_service.flush()
        else:
            self._memory_refresh_tick = 0
            self._traffic_history_tick = 0
            self._history_flush_tick = 0

        if self.api and self.stack.currentWidget() is self.connections:
            self._connection_refresh_tick += 1
            if self._connection_refresh_tick >= 2:
                self._connection_refresh_tick = 0
                self._refresh_connections()
        else:
            self._connection_refresh_tick = 0

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon)
        self.setWindowIcon(icon)
        menu = QMenu(self)
        show_action = QAction("Show Iterduca", self)
        show_action.triggered.connect(self._show_from_tray)
        self.tray_start_action = QAction("Start core", self)
        self.tray_start_action.triggered.connect(self.start_core)
        self.tray_stop_action = QAction("Stop core", self)
        self.tray_stop_action.triggered.connect(self.stop_core)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_from_tray)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(self.tray_start_action)
        menu.addAction(self.tray_stop_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self._set_tray_running(False)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _set_tray_running(self, running: bool) -> None:
        if not hasattr(self, "tray"):
            return
        state = "Core running" if running else "Core stopped"
        self.tray.setToolTip(f"Iterduca — {state}")
        if hasattr(self, "tray_start_action"):
            self.tray_start_action.setEnabled(not running)
        if hasattr(self, "tray_stop_action"):
            self.tray_stop_action.setEnabled(running)

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
        self._start_core(interactive=True, source="manual")

    def _auto_start_core(self) -> None:
        if not self.settings.auto_start_core or self.core.running:
            return
        self._log("[core] Auto-starting Mihomo Core.")
        self._start_core(interactive=False, source="auto-start")

    def _schedule_core_restart(self) -> None:
        if self._restart_scheduled or not self.settings.restart_core_on_crash:
            return
        if not self._restart_policy.allow():
            self._log(
                "[core] Automatic restart suppressed after 3 attempts within 60 seconds."
            )
            return
        self._restart_scheduled = True
        remaining = self._restart_policy.remaining()
        self._log(
            "[core] Scheduling automatic restart in 3 seconds "
            f"({remaining} attempt(s) remain in the current window)."
        )
        QTimer.singleShot(3000, self._restart_core_after_crash)

    def _restart_core_after_crash(self) -> None:
        if not self._restart_scheduled:
            return
        self._restart_scheduled = False
        if not self.settings.restart_core_on_crash or self.core.running:
            return
        self._start_core(interactive=False, source="crash recovery")

    def _start_core(self, *, interactive: bool, source: str) -> bool:
        if self.core.running:
            self._set_tray_running(True)
            return True
        try:
            executable = self.settings.core_file
            if executable is None:
                raise RuntimeError("Select or install a Mihomo executable in Settings first.")
            if not self.settings.active_profile:
                raise RuntimeError("Import and activate a profile first.")
            if self.settings.tun_enabled and not is_elevated():
                raise RuntimeError(
                    "TUN mode requires administrator privileges. "
                    "Open the TUN page and restart Iterduca as administrator."
                )
            conflicts = find_port_conflicts(
                "127.0.0.1",
                [self.settings.mixed_port, self.settings.controller_port],
            )
            if conflicts:
                formatted = ", ".join(str(port) for port in conflicts)
                raise RuntimeError(
                    f"Required local port(s) already in use: {formatted}. "
                    "Change the ports in Settings or stop the conflicting application."
                )

            profile = self.profile_service.resolve(self.settings.active_profile)
            runtime = self.runtime_builder.build(
                profile,
                mixed_port=self.settings.mixed_port,
                controller_host="127.0.0.1",
                controller_port=self.settings.controller_port,
                mode=self.settings.mode,
                overrides=self.override_service.load(),
                tun=self.settings.tun_config(),
            )
            self._controller_secret = runtime.secret
            self.core.validate(executable, runtime.path, self.paths.runtime)
            self.core.start(executable, runtime.path, self.paths.runtime)
            self._wait_for_controller()
            if self.settings.system_proxy_enabled and not self.settings.tun_enabled:
                self.system_proxy.enable("127.0.0.1", self.settings.mixed_port)
                self._system_proxy_active = True
            self._start_traffic()
            self._refresh_proxies()
            self._refresh_proxy_providers()
            self._refresh_connections()
            self._refresh_rules()
            self._refresh_rule_providers()
            self._refresh_memory()
            detail = (
                f"127.0.0.1:{self.settings.mixed_port} · "
                f"{self.settings.mode.upper()}"
            )
            self.overview.set_running(True, detail)
            self._set_tray_running(True)
            self._refresh_tun_status()
            if not interactive:
                self._log(f"[core] Mihomo Core started by {source}.")
            return True
        except Exception as exc:
            self.stop_core()
            self.overview.set_running(False, str(exc))
            if interactive:
                QMessageBox.critical(self, "Unable to start", str(exc))
            else:
                self._log(f"[core] {source} failed: {exc}")
            return False

    def stop_core(self) -> None:
        self._restart_scheduled = False
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
        self.history_service.flush()
        self._latest_traffic = (0, 0)
        self.connections.set_connections({})
        self.proxy_providers.set_providers({})
        self.rules.set_rules([])
        self.rule_providers.set_providers({})
        self.overview.set_traffic(0, 0)
        self.overview.set_memory(0)
        self.overview.set_running(False)
        self._set_tray_running(False)
        self._refresh_tun_status()

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
            self._log(f"[mode] {exc}")

    def _refresh_proxies(self) -> None:
        if not self.api:
            self.proxies.set_groups([])
            return
        try:
            self.proxies.set_groups(self.api.proxy_groups())
        except Exception as exc:
            self._log(f"[api] {exc}")

    def _select_proxy(self, group: str, proxy: str) -> None:
        if not self.api:
            return
        try:
            self.api.select_proxy(group, proxy)
            self._refresh_proxies()
        except Exception as exc:
            QMessageBox.warning(self, "Proxy switch failed", str(exc))

    def _on_traffic(self, up: int, down: int) -> None:
        self._latest_traffic = (max(0, int(up)), max(0, int(down)))
        self.overview.set_traffic(*self._latest_traffic)

    def _on_latency_result(self, group: str, proxy: str, delay: int) -> None:
        self.proxies.set_delay(group, proxy, delay)
        self.history_service.record_latency(group, proxy, delay)
        if self.proxies.current_selection() == (group, proxy):
            self._show_latency_history(group, proxy)

    def _show_latency_history(self, group: str, proxy: str) -> None:
        self.proxies.set_latency_history(
            group,
            proxy,
            self.history_service.latency(group, proxy),
        )

    def _test_latency(self, group: str, proxy: str) -> None:
        if not self.api:
            return

        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def worker() -> None:
            delay = -1
            client = MihomoApi(base, secret, timeout=6.0)
            try:
                delay = client.delay(proxy)
            except Exception as exc:
                self.bridge.log.emit(f"[latency] {proxy}: {exc}")
            finally:
                client.close()
            self.bridge.latency.emit(group, proxy, delay)

        threading.Thread(target=worker, daemon=True).start()

    def _test_latency_group(self, group: str, proxies: object) -> None:
        if not self.api or not isinstance(proxies, list):
            return

        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret
        names = [str(name) for name in proxies]

        def measure(proxy: str) -> tuple[str, int]:
            client = MihomoApi(base, secret, timeout=6.0)
            try:
                return proxy, client.delay(proxy)
            except Exception as exc:
                self.bridge.log.emit(f"[latency] {proxy}: {exc}")
                return proxy, -1
            finally:
                client.close()

        def worker() -> None:
            with ThreadPoolExecutor(max_workers=min(6, max(1, len(names)))) as pool:
                futures = [pool.submit(measure, proxy) for proxy in names]
                for future in as_completed(futures):
                    proxy, delay = future.result()
                    self.bridge.latency.emit(group, proxy, delay)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_proxy_providers(self) -> None:
        if not self.api:
            self.proxy_providers.set_providers({})
            return
        try:
            self.proxy_providers.set_providers(self.api.proxy_providers())
        except Exception as exc:
            self._log(f"[proxy-providers] {exc}")

    def _update_proxy_provider(self, name: str) -> None:
        self._run_proxy_provider_actions([name], "update")

    def _update_all_proxy_providers(self, names: object) -> None:
        if isinstance(names, list):
            self._run_proxy_provider_actions([str(name) for name in names], "update")

    def _healthcheck_proxy_provider(self, name: str) -> None:
        self._run_proxy_provider_actions([name], "healthcheck")

    def _run_proxy_provider_actions(self, names: list[str], action: str) -> None:
        if not self.api or not names:
            return
        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def execute(name: str) -> tuple[str, str | None]:
            client = MihomoApi(base, secret, timeout=20.0)
            try:
                if action == "healthcheck":
                    client.healthcheck_proxy_provider(name)
                else:
                    client.update_proxy_provider(name)
                return name, None
            except Exception as exc:
                return name, str(exc)
            finally:
                client.close()

        def worker() -> None:
            with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
                futures = [pool.submit(execute, name) for name in names]
                for future in as_completed(futures):
                    name, error = future.result()
                    if error:
                        self.bridge.proxy_provider_error.emit(f"{name}: {error}")
                    else:
                        self.bridge.proxy_provider_updated.emit(name)

        threading.Thread(target=worker, daemon=True).start()

    def _on_proxy_provider_updated(self, name: str) -> None:
        self._log(f"[proxy-providers] Updated/checked {name}")
        self._refresh_proxy_providers()
        self._refresh_proxies()

    def _on_proxy_provider_error(self, message: str) -> None:
        self._log(f"[proxy-providers] {message}")

    def _flush_dns_cache(self) -> None:
        if not self.api:
            return
        try:
            self.api.flush_dns_cache()
            self._log("[tools] DNS cache flushed.")
        except Exception as exc:
            QMessageBox.warning(self, "DNS cache", str(exc))

    def _flush_fakeip_cache(self) -> None:
        if not self.api:
            return
        try:
            self.api.flush_fakeip_cache()
            self._log("[tools] Fake-IP cache flushed.")
        except Exception as exc:
            QMessageBox.warning(self, "Fake-IP cache", str(exc))

    def _dns_query(self, name: str, record_type: str) -> None:
        if not self.api:
            self.tools.set_dns_result("Start the Mihomo core before running DNS Query.")
            return

        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def worker() -> None:
            client = MihomoApi(base, secret, timeout=5.0)
            try:
                self.bridge.dns_result.emit(client.dns_query(name, record_type))
            except Exception as exc:
                self.bridge.dns_error.emit(str(exc))
            finally:
                client.close()

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_connections(self) -> None:
        if not self.api:
            self.connections.set_connections({})
            return
        try:
            self.connections.set_connections(self.api.connections())
        except Exception as exc:
            self._log(f"[connections] {exc}")

    def _close_connection(self, connection_id: str) -> None:
        if not self.api:
            return
        try:
            self.api.close_connection(connection_id)
            self._refresh_connections()
        except Exception as exc:
            QMessageBox.warning(self, "Close connection failed", str(exc))

    def _close_all_connections(self) -> None:
        if not self.api:
            return
        try:
            self.api.close_all_connections()
            self._refresh_connections()
        except Exception as exc:
            QMessageBox.warning(self, "Close connections failed", str(exc))

    def _refresh_rules(self) -> None:
        if not self.api:
            self.rules.set_rules([])
            return
        try:
            self.rules.set_rules(self.api.rules())
        except Exception as exc:
            self._log(f"[rules] {exc}")

    def _toggle_rule(self, index: int, disabled: bool) -> None:
        if not self.api:
            return
        try:
            self.api.set_rule_disabled(index, disabled)
            self._refresh_rules()
            state = "disabled" if disabled else "enabled"
            self._log(f"[rules] Rule {index} {state} for this core session.")
        except Exception as exc:
            QMessageBox.warning(self, "Rule update failed", str(exc))

    def _refresh_rule_providers(self) -> None:
        if not self.api:
            self.rule_providers.set_providers({})
            return
        try:
            self.rule_providers.set_providers(self.api.rule_providers())
        except Exception as exc:
            self._log(f"[rule-providers] {exc}")

    def _update_rule_provider(self, name: str) -> None:
        self._run_rule_provider_updates([name])

    def _update_all_rule_providers(self, names: object) -> None:
        if isinstance(names, list):
            self._run_rule_provider_updates([str(name) for name in names])

    def _run_rule_provider_updates(self, names: list[str]) -> None:
        if not self.api or not names:
            return
        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def update(name: str) -> tuple[str, str | None]:
            client = MihomoApi(base, secret, timeout=20.0)
            try:
                client.update_rule_provider(name)
                return name, None
            except Exception as exc:
                return name, str(exc)
            finally:
                client.close()

        def worker() -> None:
            with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
                futures = [pool.submit(update, name) for name in names]
                for future in as_completed(futures):
                    name, error = future.result()
                    if error:
                        self.bridge.rule_provider_error.emit(f"{name}: {error}")
                    else:
                        self.bridge.rule_provider_updated.emit(name)

        threading.Thread(target=worker, daemon=True).start()

    def _on_rule_provider_updated(self, name: str) -> None:
        self._log(f"[rule-providers] Updated {name}")
        self._refresh_rule_providers()

    def _on_rule_provider_error(self, message: str) -> None:
        self._log(f"[rule-providers] {message}")

    def _refresh_memory(self) -> None:
        if not self.api or self._memory_request_inflight:
            return
        self._memory_request_inflight = True
        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def worker() -> None:
            client = MihomoApi(base, secret, timeout=2.0)
            try:
                memory = client.memory()
                if self.core.running:
                    self.bridge.memory.emit(memory)
            except Exception as exc:
                self.bridge.log.emit(f"[memory] {exc}")
            finally:
                client.close()
                self._memory_request_inflight = False

        threading.Thread(target=worker, daemon=True).start()

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

    def _delete_profile(self, filename: str) -> None:
        answer = QMessageBox.question(
            self,
            "Delete profile",
            f"Delete {filename}? This removes the local profile copy.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            if filename == self.settings.active_profile:
                self.stop_core()
                self.settings.active_profile = ""
                self.settings_service.save(self.settings)
            self.profile_service.delete(filename)
            self.subscription_service.forget(filename)
            self._refresh_profiles()
        except Exception as exc:
            QMessageBox.warning(self, "Delete failed", str(exc))

    def _add_subscription(self, url: str) -> None:
        self._run_subscription_task(lambda: self.subscription_service.add(url))

    def _update_subscription(self, profile_name: str) -> None:
        self._run_subscription_task(
            lambda: self.subscription_service.update(profile_name)
        )

    def _update_all_subscriptions(self, background: bool = False) -> None:
        if self._subscription_update_inflight:
            if not background:
                self._log("[subscription] An update-all task is already running.")
            return

        self._subscription_update_inflight = True

        def worker() -> None:
            try:
                infos = self.subscription_service.update_all()
                for info in infos:
                    self.bridge.subscription_ready.emit(info.profile_name)
                self.bridge.log.emit(
                    f"[subscription] Bulk update complete: {len(infos)} profile(s)."
                )
            except Exception as exc:
                if background:
                    self.bridge.log.emit(
                        f"[subscription] Automatic update failed: {exc}"
                    )
                else:
                    self.bridge.subscription_error.emit(str(exc))
            finally:
                self._subscription_update_inflight = False

        threading.Thread(target=worker, daemon=True).start()

    def _run_subscription_task(self, operation) -> None:
        def worker() -> None:
            try:
                info = operation()
                self.bridge.subscription_ready.emit(info.profile_name)
            except Exception as exc:
                self.bridge.subscription_error.emit(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_subscription_ready(self, profile_name: str) -> None:
        if not self.settings.active_profile:
            self.settings.active_profile = profile_name
            self.settings_service.save(self.settings)
        self._refresh_profiles()
        self._log(f"[subscription] Updated {profile_name}")

    def _on_subscription_error(self, message: str) -> None:
        QMessageBox.warning(self, "Subscription failed", message)

    def _refresh_profiles(self) -> None:
        subscriptions = {
            item.profile_name: item
            for item in self.subscription_service.list()
        }
        self.profiles.set_profiles(
            self.profile_service.list_profiles(),
            self.settings.active_profile,
            subscriptions,
        )

    def _load_overrides(self) -> None:
        try:
            self.overrides.set_text(self.override_service.load_text())
        except Exception as exc:
            self.overrides.set_text("# Invalid override file\n")
            self._log(f"[overrides] {exc}")

    def _save_overrides(self, text: str) -> None:
        try:
            self.override_service.save_text(text)
            self._load_overrides()
            self._log("[overrides] Saved. Restart the core to apply changes.")
        except Exception as exc:
            QMessageBox.warning(self, "Invalid overrides", str(exc))

    def _detect_core(self) -> None:
        discovered = self.core_locator.discover()
        if discovered is None:
            self.settings_page.set_core_status("Mihomo core was not found.")
            return
        self.settings.core_path = str(discovered)
        self.settings_service.save(self.settings)
        self.settings_page.set_core_path(self.settings.core_path)
        self._check_core_version(self.settings.core_path)

    def _check_core_version(self, path: str) -> None:
        if not path:
            self.settings_page.set_core_status("Select a Mihomo executable first.")
            return
        try:
            version = self.core.version(Path(path))
            self.settings_page.set_core_status(version)
        except Exception as exc:
            self.settings_page.set_core_status(f"Version check failed: {exc}")

    def _check_latest_core(self) -> None:
        if self._core_update_inflight:
            return
        self._core_update_inflight = True
        self.settings_page.set_core_update_busy(True)
        self.settings_page.set_core_update_progress(0)
        self.settings_page.set_core_update_status("Checking official Mihomo release…")

        core_path = self.settings.core_file

        def worker() -> None:
            try:
                release = self.core_update_service.latest_windows_amd64()
                current_output = ""
                if core_path is not None and core_path.is_file():
                    try:
                        current_output = self.core.version(core_path)
                    except Exception:
                        current_output = ""
                current_version = self.core_update_service.parse_version_output(
                    current_output
                )
                available = (
                    current_version is None
                    or self.core_update_service.is_newer_than_output(
                        release,
                        current_output,
                    )
                )
                self.bridge.core_release_status.emit(
                    (release, current_version, available)
                )
            except Exception as exc:
                self.bridge.core_update_error.emit(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_core_release_status(self, payload: object) -> None:
        self._core_update_inflight = False
        self.settings_page.set_core_update_busy(False)
        if not isinstance(payload, tuple) or len(payload) != 3:
            return
        release, current_version, available = payload
        if not isinstance(release, CoreRelease):
            return
        self._latest_core_release = release
        if current_version:
            state = "update available" if available else "up to date"
            text = (
                f"Current v{current_version} · latest v{release.version} · {state}"
            )
        else:
            text = f"Latest v{release.version} · no readable current Core version"
        self.settings_page.set_core_update_status(
            text,
            install_enabled=bool(available),
        )

    def _install_latest_core(self) -> None:
        if self.core.running:
            QMessageBox.warning(
                self,
                "Core update",
                "Stop the Mihomo core before installing a managed Core update.",
            )
            return
        release = self._latest_core_release
        if release is None or self._core_update_inflight:
            return

        size_mb = release.size / (1024 * 1024)
        answer = QMessageBox.question(
            self,
            "Install Mihomo Core",
            f"Download and install official Mihomo v{release.version} "
            f"({size_mb:.1f} MB)?\n\n"
            "The release asset will be SHA-256 verified before installation.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._core_update_inflight = True
        self.settings_page.set_core_update_busy(True)
        self.settings_page.set_core_update_progress(0)
        self.settings_page.set_core_update_status(
            f"Downloading Mihomo v{release.version}…"
        )

        def worker() -> None:
            try:
                path = self.core_update_service.install(
                    release,
                    self.bridge.core_update_progress.emit,
                )
                version_output = self.core.version(path)
                installed_version = (
                    self.core_update_service.parse_version_output(version_output)
                )
                if installed_version != release.version:
                    try:
                        path.unlink()
                    except OSError:
                        pass
                    try:
                        self.core_update_service.metadata_file.unlink()
                    except OSError:
                        pass
                    raise RuntimeError(
                        "Installed Mihomo version does not match the verified release"
                    )
                self.bridge.core_install_done.emit(
                    (str(path), release.version, version_output)
                )
            except Exception as exc:
                self.bridge.core_update_error.emit(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_core_install_done(self, payload: object) -> None:
        self._core_update_inflight = False
        self.settings_page.set_core_update_busy(False)
        if not isinstance(payload, tuple) or len(payload) != 3:
            return
        path, version, version_output = payload
        self.settings.core_path = str(path)
        self.settings_service.save(self.settings)
        self.settings_page.set_core_path(self.settings.core_path)
        self.settings_page.set_core_status(str(version_output))
        self.settings_page.set_core_update_progress(100)
        self.settings_page.set_core_update_status(
            f"Managed Mihomo v{version} installed and selected.",
            install_enabled=False,
        )
        self._log(f"[core-update] Installed verified Mihomo v{version}.")

    def _on_core_update_error(self, message: str) -> None:
        self._core_update_inflight = False
        self.settings_page.set_core_update_busy(False)
        self.settings_page.set_core_update_status(
            f"Core update failed: {message}",
            install_enabled=self._latest_core_release is not None,
        )
        self._log(f"[core-update] {message}")

    def _refresh_tun_status(self) -> None:
        self.tun.load_settings(
            self.settings,
            elevated=is_elevated(),
            running=self.core.running,
        )

    def _save_tun(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        was_enabled = self.settings.tun_enabled
        self.settings.tun_enabled = bool(values["tun_enabled"])
        self.settings.tun_stack = str(values["tun_stack"])
        self.settings.tun_auto_route = bool(values["tun_auto_route"])
        self.settings.tun_auto_detect_interface = bool(
            values["tun_auto_detect_interface"]
        )
        self.settings.tun_dns_hijack = bool(values["tun_dns_hijack"])
        self.settings.tun_strict_route = bool(values["tun_strict_route"])
        self.settings.tun_bypass_private_networks = bool(
            values["tun_bypass_private_networks"]
        )
        self.settings_service.save(self.settings)
        self._refresh_tun_status()

        if self.core.running and was_enabled != self.settings.tun_enabled:
            self._log("[tun] TUN mode change will apply after core restart.")
        if self.settings.tun_enabled and not is_elevated():
            QMessageBox.information(
                self,
                "TUN saved",
                "TUN is enabled for the next start. Restart Iterduca as "
                "administrator before starting the core.",
            )
        else:
            QMessageBox.information(self, "TUN", "TUN settings saved.")

    def _elevate(self) -> None:
        if is_elevated():
            self._refresh_tun_status()
            return
        if not relaunch_elevated():
            QMessageBox.warning(
                self,
                "Elevation failed",
                "Windows did not start an elevated Iterduca process.",
            )
            return
        self._force_quit = True
        self.stop_core()
        self.tray.hide()
        QApplication.quit()

    def _recover_standard_mode(self) -> None:
        self.stop_core()
        self.settings.tun_enabled = False
        self.settings_service.save(self.settings)
        self._refresh_tun_status()
        self._log(
            "[tun] TUN disabled. Iterduca returned to standard proxy mode."
        )

    def _save_settings(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        self.settings.core_path = str(values["core_path"])
        self.settings.mixed_port = int(values["mixed_port"])
        self.settings.controller_port = int(values["controller_port"])
        self.settings.mode = str(values["mode"])
        requested_proxy = bool(values["system_proxy_enabled"])
        requested_startup = bool(values["startup_enabled"])
        self.settings.auto_start_core = bool(values["auto_start_core"])
        self.settings.restart_core_on_crash = bool(values["restart_core_on_crash"])
        self.settings.subscription_auto_update_enabled = bool(
            values["subscription_auto_update_enabled"]
        )
        self.settings.subscription_update_interval_hours = int(
            values["subscription_update_interval_hours"]
        )
        self.settings.minimize_to_tray = bool(values["minimize_to_tray"])
        if requested_startup != self.settings.startup_enabled:
            try:
                self.startup_service.set_enabled(requested_startup)
                self.settings.startup_enabled = requested_startup
            except OSError as exc:
                QMessageBox.warning(self, "Startup", str(exc))
        if self.core.running and self.settings.tun_enabled:
            if self._system_proxy_active:
                self.system_proxy.disable()
                self._system_proxy_active = False
        elif self.core.running and requested_proxy != self._system_proxy_active:
            if requested_proxy:
                self.system_proxy.enable("127.0.0.1", self.settings.mixed_port)
                self._system_proxy_active = True
            else:
                self.system_proxy.disable()
                self._system_proxy_active = False
        self.settings.system_proxy_enabled = requested_proxy
        self.settings_service.save(self.settings)
        self._configure_subscription_timer()
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
