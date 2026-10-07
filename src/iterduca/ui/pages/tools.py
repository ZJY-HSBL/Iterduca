from __future__ import annotations

import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ToolsPage(QWidget):
    flush_dns_requested = pyqtSignal()
    flush_fakeip_requested = pyqtSignal()
    dns_query_requested = pyqtSignal(str, str)
    check_update_requested = pyqtSignal()
    install_update_requested = pyqtSignal()
    export_backup_requested = pyqtSignal()
    restore_backup_requested = pyqtSignal()
    export_diagnostics_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Tools")
        title.setObjectName("Title")
        layout.addWidget(title)

        hint = QLabel(
            "Maintenance and diagnostics operate on the currently running Mihomo core. "
            "They do not modify your source profile."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        maintenance = QHBoxLayout()
        dns = QPushButton("Flush DNS cache")
        fakeip = QPushButton("Flush Fake-IP cache")
        dns.clicked.connect(self.flush_dns_requested.emit)
        fakeip.clicked.connect(self.flush_fakeip_requested.emit)
        maintenance.addWidget(dns)
        maintenance.addWidget(fakeip)
        maintenance.addStretch(1)
        layout.addLayout(maintenance)

        query_row = QHBoxLayout()
        self.domain = QLineEdit()
        self.domain.setPlaceholderText("example.com")
        self.record_type = QComboBox()
        self.record_type.addItems(["A", "AAAA", "CNAME", "MX", "TXT"])
        query = QPushButton("DNS Query")
        query.clicked.connect(self._query)
        query_row.addWidget(self.domain, 1)
        query_row.addWidget(self.record_type)
        query_row.addWidget(query)
        layout.addLayout(query_row)

        self.dns_result = QPlainTextEdit()
        self.dns_result.setReadOnly(True)
        self.dns_result.setPlaceholderText("DNS response will appear here.")
        layout.addWidget(self.dns_result, 1)

        update_row = QHBoxLayout()
        check_update = QPushButton("Check for updates")
        check_update.clicked.connect(self.check_update_requested.emit)
        self.install_update = QPushButton("Download & install")
        self.install_update.setEnabled(False)
        self.install_update.clicked.connect(self.install_update_requested.emit)
        self.update_status = QLabel("Update status has not been checked.")
        self.update_status.setObjectName("Muted")
        self.update_status.setWordWrap(True)
        update_row.addWidget(check_update)
        update_row.addWidget(self.install_update)
        update_row.addWidget(self.update_status, 1)
        layout.addLayout(update_row)

        data_hint = QLabel(
            "Backup archives can contain proxy credentials from Profiles. "
            "Diagnostics archives intentionally exclude Profiles, subscription URLs, "
            "runtime configuration, controller secrets, and raw log contents."
        )
        data_hint.setObjectName("Muted")
        data_hint.setWordWrap(True)
        layout.addWidget(data_hint)

        data_row = QHBoxLayout()
        export_backup = QPushButton("Export backup")
        restore_backup = QPushButton("Restore backup")
        diagnostics = QPushButton("Export diagnostics")
        export_backup.clicked.connect(self.export_backup_requested.emit)
        restore_backup.clicked.connect(self.restore_backup_requested.emit)
        diagnostics.clicked.connect(self.export_diagnostics_requested.emit)
        data_row.addWidget(export_backup)
        data_row.addWidget(restore_backup)
        data_row.addWidget(diagnostics)
        data_row.addStretch(1)
        layout.addLayout(data_row)

    def set_dns_result(self, payload: object) -> None:
        if isinstance(payload, str):
            self.dns_result.setPlainText(payload)
            return
        self.dns_result.setPlainText(
            json.dumps(payload, ensure_ascii=False, indent=2)
        )

    def set_update_status(
        self,
        text: str,
        *,
        install_enabled: bool | None = None,
    ) -> None:
        self.update_status.setText(text)
        if install_enabled is not None:
            self.install_update.setEnabled(install_enabled)

    def _query(self) -> None:
        name = self.domain.text().strip()
        if name:
            self.dns_query_requested.emit(name, self.record_type.currentText())
