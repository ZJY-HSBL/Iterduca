from __future__ import annotations

import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ConnectionsPage(QWidget):
    refresh_requested = pyqtSignal()
    close_selected_requested = pyqtSignal(str)
    close_all_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._items: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Connections")
        title.setObjectName("Title")
        layout.addWidget(title)

        actions = QHBoxLayout()
        refresh = QPushButton("Refresh")
        close_selected = QPushButton("Close selected")
        close_all = QPushButton("Close all")
        close_all.setObjectName("DangerButton")
        refresh.clicked.connect(self.refresh_requested.emit)
        close_selected.clicked.connect(self._close_selected)
        close_all.clicked.connect(self.close_all_requested.emit)
        actions.addWidget(refresh)
        actions.addWidget(close_selected)
        actions.addWidget(close_all)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Host", "Process", "Network", "Chains", "Rule", "Upload", "Download"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._show_details)
        layout.addWidget(self.table, 3)

        detail_label = QLabel("Connection details")
        detail_label.setObjectName("Muted")
        layout.addWidget(detail_label)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumBlockCount(400)
        self.details.setPlaceholderText("Select a connection to inspect its metadata.")
        layout.addWidget(self.details, 2)

    def set_connections(self, payload: dict) -> None:
        items = payload.get("connections", [])
        rows = items if isinstance(items, list) else []
        self.table.setRowCount(0)
        self._items = []
        self.details.clear()

        for item in rows:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata", {})
            metadata = metadata if isinstance(metadata, dict) else {}
            chains = item.get("chains", [])
            chains_text = " → ".join(str(v) for v in chains) if isinstance(chains, list) else ""
            values = [
                str(metadata.get("host") or metadata.get("destinationIP") or ""),
                str(metadata.get("process") or metadata.get("processPath") or ""),
                str(metadata.get("network") or ""),
                chains_text,
                str(item.get("rule") or ""),
                self._format_bytes(item.get("upload", 0)),
                self._format_bytes(item.get("download", 0)),
            ]
            self._items.append(item)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def _close_selected(self) -> None:
        row = self.table.currentRow()
        if not 0 <= row < len(self._items):
            return
        connection_id = str(self._items[row].get("id") or "")
        if connection_id:
            self.close_selected_requested.emit(connection_id)

    def _show_details(self) -> None:
        row = self.table.currentRow()
        if not 0 <= row < len(self._items):
            self.details.clear()
            return
        self.details.setPlainText(
            json.dumps(self._items[row], ensure_ascii=False, indent=2)
        )

    @staticmethod
    def _format_bytes(value: object) -> str:
        try:
            size = float(value)
        except (TypeError, ValueError):
            size = 0.0
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
            size /= 1024
        return "0 B"
