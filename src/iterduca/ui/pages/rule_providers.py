from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class RuleProvidersPage(QWidget):
    refresh_requested = pyqtSignal()
    update_requested = pyqtSignal(str)
    update_all_requested = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._names: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Rule Providers")
        title.setObjectName("Title")
        layout.addWidget(title)

        actions = QHBoxLayout()
        refresh = QPushButton("Refresh")
        update = QPushButton("Update selected")
        update_all = QPushButton("Update all")
        refresh.clicked.connect(self.refresh_requested.emit)
        update.clicked.connect(self._update_selected)
        update_all.clicked.connect(lambda: self.update_all_requested.emit(list(self._names)))
        actions.addWidget(refresh)
        actions.addWidget(update)
        actions.addWidget(update_all)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Type", "Behavior", "Format", "Rules"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def set_providers(self, providers: dict[str, dict]) -> None:
        self.table.setRowCount(0)
        self._names = []

        for name in sorted(providers, key=str.lower):
            item = providers[name]
            self._names.append(name)
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                name,
                str(item.get("type") or item.get("vehicleType") or ""),
                str(item.get("behavior") or ""),
                str(item.get("format") or ""),
                self._rule_count(item),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def _update_selected(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self._names):
            self.update_requested.emit(self._names[row])

    @staticmethod
    def _rule_count(item: dict) -> str:
        for key in ("ruleCount", "rule-count", "count", "size"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                return str(int(value))
        return ""
