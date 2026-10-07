from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from iterduca.models.settings import AppSettings


class SettingsPage(QWidget):
    save_requested = pyqtSignal(object)
    detect_core_requested = pyqtSignal()
    check_core_requested = pyqtSignal(str)
    check_latest_core_requested = pyqtSignal()
    install_latest_core_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Settings")
        title.setObjectName("Title")
        layout.addWidget(title)

        form = QFormLayout()
        core_row = QHBoxLayout()
        self.core_path = QLineEdit()
        browse = QPushButton("Browse")
        detect = QPushButton("Detect")
        check = QPushButton("Version")
        browse.clicked.connect(self._pick_core)
        detect.clicked.connect(self.detect_core_requested.emit)
        check.clicked.connect(
            lambda: self.check_core_requested.emit(self.core_path.text().strip())
        )
        core_row.addWidget(self.core_path, 1)
        core_row.addWidget(browse)
        core_row.addWidget(detect)
        core_row.addWidget(check)
        form.addRow("Mihomo executable", core_row)

        self.core_status = QLabel("Core version not checked")
        self.core_status.setObjectName("Muted")
        form.addRow("Core status", self.core_status)

        core_update_row = QHBoxLayout()
        self.check_latest_core = QPushButton("Check latest Mihomo")
        self.install_latest_core = QPushButton("Install verified core")
        self._core_install_available = False
        self._core_update_busy = False
        self.install_latest_core.setEnabled(False)
        self.check_latest_core.clicked.connect(
            self.check_latest_core_requested.emit
        )
        self.install_latest_core.clicked.connect(
            self.install_latest_core_requested.emit
        )
        core_update_row.addWidget(self.check_latest_core)
        core_update_row.addWidget(self.install_latest_core)
        form.addRow("Core manager", core_update_row)

        self.core_update_status = QLabel("Latest Mihomo release not checked")
        self.core_update_status.setObjectName("Muted")
        self.core_update_status.setWordWrap(True)
        form.addRow("Latest release", self.core_update_status)

        self.core_update_progress = QProgressBar()
        self.core_update_progress.setRange(0, 100)
        self.core_update_progress.setValue(0)
        self.core_update_progress.setTextVisible(True)
        form.addRow("Download", self.core_update_progress)

        self.mixed_port = QSpinBox()
        self.mixed_port.setRange(1024, 65535)
        form.addRow("Mixed port", self.mixed_port)

        self.controller_port = QSpinBox()
        self.controller_port.setRange(1024, 65535)
        form.addRow("Controller port", self.controller_port)

        self.mode = QComboBox()
        self.mode.addItems(["rule", "global", "direct"])
        form.addRow("Mode", self.mode)

        self.system_proxy = QCheckBox("Enable Windows system proxy while core is running")
        form.addRow("System proxy", self.system_proxy)

        self.startup = QCheckBox("Start Iterduca with Windows")
        form.addRow("Startup", self.startup)

        self.auto_start_core = QCheckBox("Start Mihomo Core when Iterduca launches")
        form.addRow("Core startup", self.auto_start_core)

        self.restart_core_on_crash = QCheckBox(
            "Restart Mihomo after an unexpected exit (max 3 attempts / minute)"
        )
        form.addRow("Core recovery", self.restart_core_on_crash)

        self.subscription_auto_update = QCheckBox(
            "Automatically update all subscriptions"
        )
        form.addRow("Subscriptions", self.subscription_auto_update)

        self.subscription_interval = QSpinBox()
        self.subscription_interval.setRange(1, 168)
        self.subscription_interval.setSuffix(" h")
        form.addRow("Update interval", self.subscription_interval)

        self.minimize_to_tray = QCheckBox("Close button minimizes Iterduca to the system tray")
        form.addRow("Window behavior", self.minimize_to_tray)
        layout.addLayout(form)

        save = QPushButton("Save settings")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._save)
        layout.addWidget(save)
        layout.addStretch(1)

    def load_settings(self, settings: AppSettings) -> None:
        self.core_path.setText(settings.core_path)
        self.mixed_port.setValue(settings.mixed_port)
        self.controller_port.setValue(settings.controller_port)
        index = self.mode.findText(settings.mode.lower())
        self.mode.setCurrentIndex(max(0, index))
        self.system_proxy.setChecked(settings.system_proxy_enabled)
        self.startup.setChecked(settings.startup_enabled)
        self.auto_start_core.setChecked(settings.auto_start_core)
        self.restart_core_on_crash.setChecked(settings.restart_core_on_crash)
        self.subscription_auto_update.setChecked(
            settings.subscription_auto_update_enabled
        )
        self.subscription_interval.setValue(
            settings.subscription_update_interval_hours
        )
        self.minimize_to_tray.setChecked(settings.minimize_to_tray)

    def set_core_status(self, text: str) -> None:
        self.core_status.setText(text)

    def set_core_path(self, path: str) -> None:
        self.core_path.setText(path)

    def set_core_update_status(
        self,
        text: str,
        *,
        install_enabled: bool = False,
    ) -> None:
        self._core_install_available = install_enabled
        self.core_update_status.setText(text)
        self.install_latest_core.setEnabled(
            install_enabled and not self._core_update_busy
        )

    def set_core_update_progress(self, value: int) -> None:
        self.core_update_progress.setValue(max(0, min(100, int(value))))

    def set_core_update_busy(self, busy: bool) -> None:
        self._core_update_busy = busy
        self.check_latest_core.setEnabled(not busy)
        self.install_latest_core.setEnabled(
            self._core_install_available and not busy
        )

    def _pick_core(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Mihomo executable")
        if path:
            self.core_path.setText(path)

    def _save(self) -> None:
        self.save_requested.emit(
            {
                "core_path": self.core_path.text().strip(),
                "mixed_port": self.mixed_port.value(),
                "controller_port": self.controller_port.value(),
                "mode": self.mode.currentText(),
                "system_proxy_enabled": self.system_proxy.isChecked(),
                "startup_enabled": self.startup.isChecked(),
                "auto_start_core": self.auto_start_core.isChecked(),
                "restart_core_on_crash": self.restart_core_on_crash.isChecked(),
                "subscription_auto_update_enabled": (
                    self.subscription_auto_update.isChecked()
                ),
                "subscription_update_interval_hours": (
                    self.subscription_interval.value()
                ),
                "minimize_to_tray": self.minimize_to_tray.isChecked(),
            }
        )
