from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _format_rate(value: int) -> str:
    size = float(max(0, value))
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if size < 1024 or unit == "GB/s":
            return f"{size:.1f} {unit}"
        size /= 1024
    return "0 B/s"


class OverviewPage(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Overview")
        title.setObjectName("Title")
        layout.addWidget(title)

        status_card = QFrame()
        status_card.setObjectName("Card")
        status_layout = QVBoxLayout(status_card)
        self.status = QLabel("Core stopped")
        self.status.setObjectName("Metric")
        self.detail = QLabel("Select a profile and Mihomo executable to begin.")
        self.detail.setObjectName("Muted")
        status_layout.addWidget(self.status)
        status_layout.addWidget(self.detail)
        layout.addWidget(status_card)

        traffic = QFrame()
        traffic.setObjectName("Card")
        traffic_layout = QGridLayout(traffic)
        traffic_layout.addWidget(QLabel("Upload"), 0, 0)
        traffic_layout.addWidget(QLabel("Download"), 0, 1)
        self.upload = QLabel("0 B/s")
        self.download = QLabel("0 B/s")
        self.upload.setObjectName("Metric")
        self.download.setObjectName("Metric")
        traffic_layout.addWidget(self.upload, 1, 0)
        traffic_layout.addWidget(self.download, 1, 1)
        layout.addWidget(traffic)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Routing mode"))
        self.mode = QComboBox()
        self.mode.addItems(["rule", "global", "direct"])
        self.mode.currentTextChanged.connect(self.mode_changed.emit)
        mode_row.addWidget(self.mode, 1)
        layout.addLayout(mode_row)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Start core")
        self.start_button.setObjectName("PrimaryButton")
        self.stop_button = QPushButton("Stop core")
        self.stop_button.setObjectName("DangerButton")
        self.stop_button.setEnabled(False)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        layout.addLayout(actions)
        layout.addStretch(1)

    def set_running(self, running: bool, detail: str = "") -> None:
        self.status.setText("Connected" if running else "Core stopped")
        self.detail.setText(detail or ("Mihomo is running." if running else "Core is not running."))
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)

    def set_mode(self, mode: str) -> None:
        self.mode.blockSignals(True)
        index = self.mode.findText(mode.lower())
        self.mode.setCurrentIndex(max(0, index))
        self.mode.blockSignals(False)

    def set_traffic(self, up: int, down: int) -> None:
        self.upload.setText(_format_rate(up))
        self.download.setText(_format_rate(down))
