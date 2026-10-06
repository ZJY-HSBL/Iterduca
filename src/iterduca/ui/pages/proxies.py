from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iterduca.core.api import ProxyGroup


class ProxiesPage(QWidget):
    proxy_selected = pyqtSignal(str, str)
    latency_requested = pyqtSignal(str, str)
    refresh_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Proxies")
        title.setObjectName("Title")
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Group"))
        self.groups = QComboBox()
        self.refresh = QPushButton("Refresh")
        self.test_latency = QPushButton("Test latency")
        controls.addWidget(self.groups, 1)
        controls.addWidget(self.test_latency)
        controls.addWidget(self.refresh)
        layout.addLayout(controls)

        hint = QLabel("Double-click a node to select it.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self.nodes = QListWidget()
        layout.addWidget(self.nodes, 1)

        self.groups.currentIndexChanged.connect(self._show_group)
        self.nodes.itemDoubleClicked.connect(self._select_current)
        self.test_latency.clicked.connect(self._test_current)
        self.refresh.clicked.connect(self.refresh_requested.emit)

        self._data: list[ProxyGroup] = []
        self._delays: dict[tuple[str, str], int] = {}

    def set_groups(self, groups: list[ProxyGroup]) -> None:
        current_name = self.groups.currentText()
        self._data = groups
        self.groups.blockSignals(True)
        self.groups.clear()
        self.groups.addItems([group.name for group in groups])
        if current_name:
            index = self.groups.findText(current_name)
            if index >= 0:
                self.groups.setCurrentIndex(index)
        self.groups.blockSignals(False)
        self._show_group()

    def set_delay(self, group: str, proxy: str, delay: int) -> None:
        self._delays[(group, proxy)] = delay
        if self.groups.currentText() == group:
            self._show_group()

    def _show_group(self) -> None:
        self.nodes.clear()
        index = self.groups.currentIndex()
        if index < 0 or index >= len(self._data):
            return

        group = self._data[index]
        for name in group.all:
            parts = [name]
            if name == group.now:
                parts.append("✓")
            delay = self._delays.get((group.name, name))
            if delay is not None:
                parts.append("timeout" if delay < 0 else f"{delay} ms")
            self.nodes.addItem("    ".join(parts))

    def _select_current(self) -> None:
        selected = self._current()
        if selected:
            self.proxy_selected.emit(*selected)

    def _test_current(self) -> None:
        selected = self._current()
        if selected:
            self.latency_requested.emit(*selected)

    def _current(self) -> tuple[str, str] | None:
        group_index = self.groups.currentIndex()
        node_index = self.nodes.currentRow()
        if group_index < 0 or node_index < 0:
            return None
        group = self._data[group_index]
        if node_index >= len(group.all):
            return None
        return group.name, group.all[node_index]
