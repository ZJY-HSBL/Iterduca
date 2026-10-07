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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from iterduca.models.settings import AppSettings


class SettingsPage(QWidget):
    save_requested = pyqtSignal(object)
    detect_core_requested = pyqtSignal()
    check_core_requested = pyqtSignal(str)

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
                "subscription_auto_update_enabled": (
                    self.subscription_auto_update.isChecked()
                ),
                "subscription_update_interval_hours": (
                    self.subscription_interval.value()
                ),
                "minimize_to_tray": self.minimize_to_tray.isChecked(),
            }
        )
