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
from iterduca.ui.widgets.sparkline import Sparkline


class ProxiesPage(QWidget):
    proxy_selected = pyqtSignal(str, str)
    latency_requested = pyqtSignal(str, str)
    latency_group_requested = pyqtSignal(str, object)
    history_requested = pyqtSignal(str, str)
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
        self.test_group = QPushButton("Test group")
        controls.addWidget(self.groups, 1)
        controls.addWidget(self.test_latency)
        controls.addWidget(self.test_group)
        controls.addWidget(self.refresh)
        layout.addLayout(controls)

        hint = QLabel("Double-click a node to select it.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self.nodes = QListWidget()
        layout.addWidget(self.nodes, 2)

        history_label = QLabel("Latency history")
        history_label.setObjectName("Muted")
        layout.addWidget(history_label)
        self.history_title = QLabel("Select a node to view its latency history.")
        self.history_title.setObjectName("Muted")
        layout.addWidget(self.history_title)
        self.latency_chart = Sparkline()
        layout.addWidget(self.latency_chart, 1)

        self.groups.currentIndexChanged.connect(self._show_group)
        self.nodes.itemDoubleClicked.connect(self._select_current)
        self.nodes.currentRowChanged.connect(self._request_history)
        self.test_latency.clicked.connect(self._test_current)
        self.test_group.clicked.connect(self._test_group)
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

    def _test_group(self) -> None:
        index = self.groups.currentIndex()
        if 0 <= index < len(self._data):
            group = self._data[index]
            self.latency_group_requested.emit(group.name, list(group.all))

    def set_latency_history(
        self,
        group: str,
        proxy: str,
        samples: list[dict],
    ) -> None:
        delays = [
            int(item.get("delay", -1))
            for item in samples
            if isinstance(item, dict) and int(item.get("delay", -1)) >= 0
        ]
        self.history_title.setText(
            f"{group} / {proxy} · {len(samples)} recorded sample(s)"
        )
        self.latency_chart.set_series(delays)

    def _request_history(self) -> None:
        selected = self._current()
        if selected:
            self.history_requested.emit(*selected)
        else:
            self.history_title.setText("Select a node to view its latency history.")
            self.latency_chart.clear()

    def _current(self) -> tuple[str, str] | None:
        group_index = self.groups.currentIndex()
        node_index = self.nodes.currentRow()
        if group_index < 0 or node_index < 0:
            return None
        group = self._data[group_index]
        if node_index >= len(group.all):
            return None
        return group.name, group.all[node_index]
