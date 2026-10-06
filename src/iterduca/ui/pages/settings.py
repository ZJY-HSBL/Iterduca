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
        browse.clicked.connect(self._pick_core)
        core_row.addWidget(self.core_path, 1)
        core_row.addWidget(browse)
        form.addRow("Mihomo executable", core_row)

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
            }
        )
