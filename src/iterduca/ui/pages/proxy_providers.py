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


class ProxyProvidersPage(QWidget):
    refresh_requested = pyqtSignal()
    update_requested = pyqtSignal(str)
    update_all_requested = pyqtSignal(object)
    healthcheck_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._names: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Proxy Providers")
        title.setObjectName("Title")
        layout.addWidget(title)

        actions = QHBoxLayout()
        refresh = QPushButton("Refresh")
        update = QPushButton("Update selected")
        update_all = QPushButton("Update all")
        healthcheck = QPushButton("Healthcheck")
        refresh.clicked.connect(self.refresh_requested.emit)
        update.clicked.connect(self._update_selected)
        update_all.clicked.connect(lambda: self.update_all_requested.emit(list(self._names)))
        healthcheck.clicked.connect(self._healthcheck_selected)
        actions.addWidget(refresh)
        actions.addWidget(update)
        actions.addWidget(update_all)
        actions.addWidget(healthcheck)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Proxies", "Alive"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

    def set_providers(self, providers: dict[str, dict]) -> None:
        self.table.setRowCount(0)
        self._names = []

        for name in sorted(providers, key=str.lower):
            item = providers[name]
            proxies = item.get("proxies", [])
            proxy_items = proxies if isinstance(proxies, list) else []
            alive = sum(
                1
                for proxy in proxy_items
                if isinstance(proxy, dict) and proxy.get("alive") is True
            )

            self._names.append(name)
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                name,
                str(item.get("type") or item.get("vehicleType") or ""),
                str(len(proxy_items)),
                f"{alive}/{len(proxy_items)}" if proxy_items else "",
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def _update_selected(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self._names):
            self.update_requested.emit(self._names[row])

    def _healthcheck_selected(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self._names):
            self.healthcheck_requested.emit(self._names[row])
