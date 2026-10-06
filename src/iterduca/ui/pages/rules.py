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
    toggle_requested = pyqtSignal(int, bool)

    def __init__(self) -> None:
        super().__init__()
        self._rules: list[dict] = []
        self._visible_rules: list[dict] = []

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
        toggle = QPushButton("Toggle selected")
        refresh.clicked.connect(self.refresh_requested.emit)
        toggle.clicked.connect(self._toggle_selected)
        self.search.textChanged.connect(self._render)
        controls.addWidget(self.search, 1)
        controls.addWidget(toggle)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        hint = QLabel("Rule disable state is temporary and resets when Mihomo restarts.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Index", "State", "Type", "Payload", "Proxy", "Hits"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def set_rules(self, rules: list[dict]) -> None:
        self._rules = rules
        self._render()

    def _render(self) -> None:
        query = self.search.text().strip().lower()
        self.table.setRowCount(0)
        self._visible_rules = []

        for item in self._rules:
            extra = item.get("extra", {})
            extra = extra if isinstance(extra, dict) else {}
            disabled = bool(extra.get("disabled", False))
            values = [
                str(item.get("index", "")),
                "Disabled" if disabled else "Enabled",
                str(item.get("type", "")),
                str(item.get("payload", "")),
                str(item.get("proxy", "")),
                str(extra.get("hitCount", "")),
            ]
            if query and query not in " ".join(values).lower():
                continue
            self._visible_rules.append(item)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def _toggle_selected(self) -> None:
        row = self.table.currentRow()
        if not 0 <= row < len(self._visible_rules):
            return
        item = self._visible_rules[row]
        index = item.get("index")
        if not isinstance(index, int):
            return
        extra = item.get("extra", {})
        extra = extra if isinstance(extra, dict) else {}
        disabled = bool(extra.get("disabled", False))
        self.toggle_requested.emit(index, not disabled)
