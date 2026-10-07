from __future__ import annotations

import json

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SortableItem(QTableWidgetItem):
    def __init__(self, text: str, sort_value: object | None = None) -> None:
        super().__init__(text)
        self.sort_value = text if sort_value is None else sort_value

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, SortableItem):
            try:
                return self.sort_value < other.sort_value
            except TypeError:
                return str(self.sort_value) < str(other.sort_value)
        return super().__lt__(other)


class ConnectionsPage(QWidget):
    refresh_requested = pyqtSignal()
    close_selected_requested = pyqtSignal(str)
    close_all_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Connections")
        title.setObjectName("Title")
        layout.addWidget(title)

        actions = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search host, process, rule, chain or network")
        self.search.textChanged.connect(self._apply_filter)
        refresh = QPushButton("Refresh")
        close_selected = QPushButton("Close selected")
        close_all = QPushButton("Close all")
        close_all.setObjectName("DangerButton")
        refresh.clicked.connect(self.refresh_requested.emit)
        close_selected.clicked.connect(self._close_selected)
        close_all.clicked.connect(self.close_all_requested.emit)
        actions.addWidget(self.search, 1)
        actions.addWidget(refresh)
        actions.addWidget(close_selected)
        actions.addWidget(close_all)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Host", "Process", "Network", "Chains", "Rule", "Upload", "Download"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
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

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.details.clear()

        for item in rows:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata", {})
            metadata = metadata if isinstance(metadata, dict) else {}
            chains = item.get("chains", [])
            chains_text = " → ".join(str(v) for v in chains) if isinstance(chains, list) else ""
            upload = self._number(item.get("upload", 0))
            download = self._number(item.get("download", 0))
            values: list[tuple[str, object]] = [
                (str(metadata.get("host") or metadata.get("destinationIP") or ""), ""),
                (str(metadata.get("process") or metadata.get("processPath") or ""), ""),
                (str(metadata.get("network") or ""), ""),
                (chains_text, ""),
                (str(item.get("rule") or ""), ""),
                (self._format_bytes(upload), upload),
                (self._format_bytes(download), download),
            ]

            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, (text, sort_value) in enumerate(values):
                cell = SortableItem(text, sort_value if sort_value != "" else text.lower())
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, item)
                self.table.setItem(row, column, cell)

        self.table.setSortingEnabled(True)
        self._apply_filter()

    def _close_selected(self) -> None:
        item = self._selected_payload()
        if item is None:
            return
        connection_id = str(item.get("id") or "")
        if connection_id:
            self.close_selected_requested.emit(connection_id)

    def _show_details(self) -> None:
        item = self._selected_payload()
        if item is None:
            self.details.clear()
            return
        self.details.setPlainText(json.dumps(item, ensure_ascii=False, indent=2))

    def _selected_payload(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        first = self.table.item(row, 0)
        if first is None:
            return None
        payload = first.data(Qt.ItemDataRole.UserRole)
        return payload if isinstance(payload, dict) else None

    def _apply_filter(self) -> None:
        query = self.search.text().strip().lower()
        for row in range(self.table.rowCount()):
            haystack = " ".join(
                self.table.item(row, column).text()
                for column in range(self.table.columnCount())
                if self.table.item(row, column) is not None
            ).lower()
            self.table.setRowHidden(row, bool(query and query not in haystack))

    @staticmethod
    def _number(value: object) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _format_bytes(value: object) -> str:
        size = float(ConnectionsPage._number(value))
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
            size /= 1024
        return "0 B"
