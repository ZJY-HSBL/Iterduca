from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iterduca.core.api import ProxyGroup
from iterduca.services.proxy_view import (
    SORT_LATENCY,
    SORT_NAME,
    SORT_PROFILE,
    arrange_proxy_names,
)
from iterduca.ui.widgets.sparkline import Sparkline


class ProxiesPage(QWidget):
    proxy_selected = pyqtSignal(str, str)
    latency_requested = pyqtSignal(str, str)
    latency_group_requested = pyqtSignal(str, object)
    history_requested = pyqtSignal(str, str)
    refresh_requested = pyqtSignal()

    SORT_OPTIONS = {
        "Profile order": SORT_PROFILE,
        "Name A–Z": SORT_NAME,
        "Latency fastest": SORT_LATENCY,
    }

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
        self.test_latency = QPushButton("Test selected")
        self.test_group = QPushButton("Test group")
        controls.addWidget(self.groups, 1)
        controls.addWidget(self.test_latency)
        controls.addWidget(self.test_group)
        controls.addWidget(self.refresh)
        layout.addLayout(controls)

        filter_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search nodes")
        self.sort = QComboBox()
        self.sort.addItems(list(self.SORT_OPTIONS))
        self.test_visible = QPushButton("Test visible")
        filter_row.addWidget(self.search, 1)
        filter_row.addWidget(QLabel("Sort"))
        filter_row.addWidget(self.sort)
        filter_row.addWidget(self.test_visible)
        layout.addLayout(filter_row)

        self.summary = QLabel("No proxy group loaded.")
        self.summary.setObjectName("Muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        hint = QLabel("Double-click a visible node to select it.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self.nodes = QListWidget()
        layout.addWidget(self.nodes, 2)

        history_label = QLabel("Latency history")
        history_label.setObjectName("Muted")
        layout.addWidget(history_label)
        self.history_title = QLabel("Select a node to view its latency history.")
        self.history_title.setObjectName("Muted")
        self.history_title.setWordWrap(True)
        layout.addWidget(self.history_title)
        self.latency_chart = Sparkline()
        layout.addWidget(self.latency_chart, 1)

        self.groups.currentIndexChanged.connect(self._show_group)
        self.search.textChanged.connect(self._show_group)
        self.sort.currentIndexChanged.connect(self._show_group)
        self.nodes.itemDoubleClicked.connect(self._select_current)
        self.nodes.currentRowChanged.connect(self._request_history)
        self.test_latency.clicked.connect(self._test_current)
        self.test_group.clicked.connect(self._test_group)
        self.test_visible.clicked.connect(self._test_visible)
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
        self._delays[(group, proxy)] = int(delay)
        if self.groups.currentText() == group:
            self._show_group()

    def _show_group(self) -> None:
        previous = self._current()
        group = self._current_group()

        self.nodes.blockSignals(True)
        self.nodes.clear()

        if group is None:
            self.nodes.blockSignals(False)
            self.summary.setText("No proxy group loaded.")
            self.history_title.setText("Select a node to view its latency history.")
            self.latency_chart.clear()
            return

        delay_map = {
            name: delay
            for (group_name, name), delay in self._delays.items()
            if group_name == group.name
        }
        sort_mode = self.SORT_OPTIONS.get(
            self.sort.currentText(),
            SORT_PROFILE,
        )
        visible = arrange_proxy_names(
            group.all,
            query=self.search.text(),
            sort_mode=sort_mode,
            delays=delay_map,
        )

        preferred = ""
        if previous is not None and previous[0] == group.name:
            preferred = previous[1]
        elif group.now:
            preferred = group.now

        selected_row = -1
        for name in visible:
            delay = self._delays.get((group.name, name))
            parts = [name]
            if name == group.now:
                parts.append("CURRENT")
            if delay is not None:
                parts.append("timeout" if delay < 0 else f"{delay} ms")

            item = QListWidgetItem("    ".join(parts))
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.nodes.addItem(item)
            if name == preferred:
                selected_row = self.nodes.count() - 1

        if selected_row >= 0:
            self.nodes.setCurrentRow(selected_row)
        self.nodes.blockSignals(False)

        tested = sum(
            1
            for name in group.all
            if (group.name, name) in self._delays
        )
        successful = sum(
            1
            for name in group.all
            if self._delays.get((group.name, name), -1) >= 0
            and (group.name, name) in self._delays
        )
        current = group.now or "—"
        kind = group.kind or "Proxy group"
        self.summary.setText(
            f"{kind} · Current {current} · Showing {len(visible)}/{len(group.all)} "
            f"· Tested {tested}/{len(group.all)} · Reachable {successful}"
        )
        self._request_history()

    def _select_current(self) -> None:
        selected = self._current()
        if selected:
            self.proxy_selected.emit(*selected)

    def _test_current(self) -> None:
        selected = self._current()
        if selected:
            self.latency_requested.emit(*selected)

    def _test_group(self) -> None:
        group = self._current_group()
        if group is not None:
            self.latency_group_requested.emit(group.name, list(group.all))

    def _test_visible(self) -> None:
        group = self._current_group()
        if group is None:
            return
        names = [
            str(self.nodes.item(row).data(Qt.ItemDataRole.UserRole))
            for row in range(self.nodes.count())
        ]
        if names:
            self.latency_group_requested.emit(group.name, names)

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
        if delays:
            minimum = min(delays)
            maximum = max(delays)
            average = round(sum(delays) / len(delays))
            statistics = (
                f"min {minimum} ms · avg {average} ms · max {maximum} ms"
            )
        else:
            statistics = "no successful latency samples"

        self.history_title.setText(
            f"{group} / {proxy} · {len(samples)} recorded sample(s) · {statistics}"
        )
        self.latency_chart.set_series(delays)

    def _request_history(self) -> None:
        selected = self._current()
        if selected:
            self.history_requested.emit(*selected)
        else:
            self.history_title.setText("Select a node to view its latency history.")
            self.latency_chart.clear()

    def current_selection(self) -> tuple[str, str] | None:
        return self._current()

    def _current_group(self) -> ProxyGroup | None:
        index = self.groups.currentIndex()
        if 0 <= index < len(self._data):
            return self._data[index]
        return None

    def _current(self) -> tuple[str, str] | None:
        group = self._current_group()
        item = self.nodes.currentItem()
        if group is None or item is None:
            return None
        name = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(name, str) or not name:
            return None
        return group.name, name
