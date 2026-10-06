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
from iterduca.services.core_locator import CoreLocator
from iterduca.services.override_service import OverrideService
from iterduca.services.profile_service import ProfileService
from iterduca.services.settings_service import SettingsService
from iterduca.services.subscription_service import SubscriptionService
from iterduca.system.privilege import is_elevated, relaunch_elevated
from iterduca.system.proxy import SystemProxy
from iterduca.system.startup import StartupService
from iterduca.ui.pages.connections import ConnectionsPage
from iterduca.ui.pages.logs import LogsPage
from iterduca.ui.pages.overrides import OverridesPage
from iterduca.ui.pages.overview import OverviewPage
from iterduca.ui.pages.profiles import ProfilesPage
from iterduca.ui.pages.proxies import ProxiesPage
from iterduca.ui.pages.rule_providers import RuleProvidersPage
from iterduca.ui.pages.rules import RulesPage
from iterduca.ui.pages.settings import SettingsPage
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
        self.settings = self.settings_service.load()
        self.core_locator = CoreLocator()
        if not self.settings.core_path:
            discovered_core = self.core_locator.discover()
            if discovered_core is not None:
                self.settings.core_path = str(discovered_core)
                self.settings_service.save(self.settings)
        self.startup_service = StartupService()
        if self.startup_service.supported:
            self.settings.startup_enabled = self.startup_service.is_enabled()
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
        self._load_overrides()
        self._refresh_tun_status()
        self._build_health_timer()

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
        self.connections = ConnectionsPage()
        self.rules = RulesPage()
        self.rule_providers = RuleProvidersPage()
        self.overrides = OverridesPage()
        self.tun = TunPage()
        self.logs = LogsPage()
        self.settings_page = SettingsPage()
        pages = [
            ("Overview", self.overview),
            ("Proxies", self.proxies),
            ("Profiles", self.profiles),
            ("Connections", self.connections),
            ("Rules", self.rules),
            ("Rule Providers", self.rule_providers),
            ("Overrides", self.overrides),
            ("TUN", self.tun),
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
        version = QLabel("v0.5.0")
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
        self.proxies.refresh_requested.connect(self._refresh_proxies)
        self.proxies.proxy_selected.connect(self._select_proxy)
        self.proxies.latency_requested.connect(self._test_latency)
        self.proxies.latency_group_requested.connect(self._test_latency_group)
        self.connections.refresh_requested.connect(self._refresh_connections)
        self.connections.close_selected_requested.connect(self._close_connection)
        self.connections.close_all_requested.connect(self._close_all_connections)
        self.rules.refresh_requested.connect(self._refresh_rules)
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
        self.bridge.log.connect(self.logs.append)
        self.bridge.traffic.connect(self.overview.set_traffic)
        self.bridge.latency.connect(self.proxies.set_delay)
        self.bridge.subscription_ready.connect(self._on_subscription_ready)
        self.bridge.subscription_error.connect(self._on_subscription_error)
        self.bridge.memory.connect(self.overview.set_memory)
        self.bridge.rule_provider_updated.connect(self._on_rule_provider_updated)
        self.bridge.rule_provider_error.connect(self._on_rule_provider_error)

    def _build_health_timer(self) -> None:
        self._connection_refresh_tick = 0
        self._memory_refresh_tick = 0
        self._memory_request_inflight = False
        self.health_timer = QTimer(self)
        self.health_timer.setInterval(1000)
        self.health_timer.timeout.connect(self._poll_core_state)
        self.health_timer.start()

    def _poll_core_state(self) -> None:
        has_runtime_state = (
            self.api is not None
            or self.traffic_monitor is not None
            or self._system_proxy_active
        )
        if has_runtime_state and not self.core.running:
            self.logs.append("[core] Mihomo exited unexpectedly; runtime state restored.")
            self.stop_core()
            return

        if self.api:
            self._memory_refresh_tick += 1
            if self._memory_refresh_tick >= 2:
                self._memory_refresh_tick = 0
                self._refresh_memory()
        else:
            self._memory_refresh_tick = 0

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
            if self.settings.tun_enabled and not is_elevated():
                raise RuntimeError(
                    "TUN mode requires administrator privileges. "
                    "Open the TUN page and restart Iterduca as administrator."
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
            self._refresh_connections()
            self._refresh_rules()
            self._refresh_rule_providers()
            self._refresh_memory()
            detail = (
                f"127.0.0.1:{self.settings.mixed_port} · "
                f"{self.settings.mode.upper()}"
            )
            self.overview.set_running(True, detail)
            self._refresh_tun_status()
        except Exception as exc:
            self.stop_core()
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
        self.connections.set_connections({})
        self.rules.set_rules([])
        self.rule_providers.set_providers({})
        self.overview.set_traffic(0, 0)
        self.overview.set_memory(0)
        self.overview.set_running(False)
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

    def _refresh_connections(self) -> None:
        if not self.api:
            self.connections.set_connections({})
            return
        try:
            self.connections.set_connections(self.api.connections())
        except Exception as exc:
            self.logs.append(f"[connections] {exc}")

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
            self.logs.append(f"[rules] {exc}")

    def _refresh_rule_providers(self) -> None:
        if not self.api:
            self.rule_providers.set_providers({})
            return
        try:
            self.rule_providers.set_providers(self.api.rule_providers())
        except Exception as exc:
            self.logs.append(f"[rule-providers] {exc}")

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
        self.logs.append(f"[rule-providers] Updated {name}")
        self._refresh_rule_providers()

    def _on_rule_provider_error(self, message: str) -> None:
        self.logs.append(f"[rule-providers] {message}")

    def _refresh_memory(self) -> None:
        if not self.api or self._memory_request_inflight:
            return
        self._memory_request_inflight = True
        base = f"http://127.0.0.1:{self.settings.controller_port}"
        secret = self._controller_secret

        def worker() -> None:
            client = MihomoApi(base, secret, timeout=2.0)
            try:
                self.bridge.memory.emit(client.memory())
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

    def _update_all_subscriptions(self) -> None:
        def worker() -> None:
            try:
                infos = self.subscription_service.update_all()
                for info in infos:
                    self.bridge.subscription_ready.emit(info.profile_name)
                self.bridge.log.emit(
                    f"[subscription] Bulk update complete: {len(infos)} profile(s)."
                )
            except Exception as exc:
                self.bridge.subscription_error.emit(str(exc))

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
        self.logs.append(f"[subscription] Updated {profile_name}")

    def _on_subscription_error(self, message: str) -> None:
        QMessageBox.warning(self, "Subscription failed", message)

    def _refresh_profiles(self) -> None:
        subscription_names = {
            item.profile_name for item in self.subscription_service.list()
        }
        self.profiles.set_profiles(
            self.profile_service.list_profiles(),
            self.settings.active_profile,
            subscription_names,
        )

    def _load_overrides(self) -> None:
        try:
            self.overrides.set_text(self.override_service.load_text())
        except Exception as exc:
            self.overrides.set_text("# Invalid override file\n")
            self.logs.append(f"[overrides] {exc}")

    def _save_overrides(self, text: str) -> None:
        try:
            self.override_service.save_text(text)
            self._load_overrides()
            self.logs.append("[overrides] Saved. Restart the core to apply changes.")
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
            self.logs.append("[tun] TUN mode change will apply after core restart.")
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
        self.logs.append(
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
