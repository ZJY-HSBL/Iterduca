from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ToolsPage(QWidget):
    flush_dns_requested = pyqtSignal()
    flush_fakeip_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Tools")
        title.setObjectName("Title")
        layout.addWidget(title)

        hint = QLabel(
            "Maintenance actions operate on the currently running Mihomo core. "
            "Cache flushes do not modify your source profile."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        dns = QPushButton("Flush DNS cache")
        fakeip = QPushButton("Flush Fake-IP cache")
        dns.clicked.connect(self.flush_dns_requested.emit)
        fakeip.clicked.connect(self.flush_fakeip_requested.emit)
        layout.addWidget(dns)
        layout.addWidget(fakeip)
        layout.addStretch(1)
