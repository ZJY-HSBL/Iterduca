from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class RulesPage(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._rules: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Rules")
        title.setObjectName("Title")
        layout.addWidget(title)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter type, payload or proxy")
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_requested.emit)
        self.search.textChanged.connect(self._render)
        controls.addWidget(self.search, 1)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Payload", "Proxy"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def set_rules(self, rules: list[dict]) -> None:
        self._rules = rules
        self._render()

    def _render(self) -> None:
        query = self.search.text().strip().lower()
        self.table.setRowCount(0)
        for item in self._rules:
            values = [
                str(item.get("type", "")),
                str(item.get("payload", "")),
                str(item.get("proxy", "")),
            ]
            if query and query not in " ".join(values).lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
