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
        controls.addWidget(self.groups, 1)
        controls.addWidget(self.refresh)
        layout.addLayout(controls)

        self.nodes = QListWidget()
        layout.addWidget(self.nodes, 1)
        self.groups.currentIndexChanged.connect(self._show_group)
        self.nodes.itemDoubleClicked.connect(self._select_current)
        self.refresh.clicked.connect(self.refresh_requested.emit)
        self._data: list[ProxyGroup] = []

    def set_groups(self, groups: list[ProxyGroup]) -> None:
        self._data = groups
        self.groups.blockSignals(True)
        self.groups.clear()
        self.groups.addItems([group.name for group in groups])
        self.groups.blockSignals(False)
        self._show_group()

    def _show_group(self) -> None:
        self.nodes.clear()
        index = self.groups.currentIndex()
        if index < 0 or index >= len(self._data):
            return
        group = self._data[index]
        for name in group.all:
            suffix = "  ✓" if name == group.now else ""
            self.nodes.addItem(f"{name}{suffix}")

    def _select_current(self) -> None:
        group_index = self.groups.currentIndex()
        node_index = self.nodes.currentRow()
        if group_index < 0 or node_index < 0:
            return
        group = self._data[group_index]
        if node_index >= len(group.all):
            return
        self.proxy_selected.emit(group.name, group.all[node_index])
