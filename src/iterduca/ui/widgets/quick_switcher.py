"""Ctrl+K page switcher backed by actual sidebar destinations."""
from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from iterduca.services.navigation_service import (
    NavigationItem,
    search_navigation,
)


class QuickSwitcher(QDialog):
    def __init__(
        self, destinations: Sequence[NavigationItem], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.destinations = list(destinations)
        self.selected_index: int | None = None
        self.setWindowTitle("Quick navigation")
        self.setMinimumWidth(420)
        self.resize(480, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        title = QLabel("Jump to a page")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search pages or groups…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._update_results)
        self.search.returnPressed.connect(self._choose_selected)
        layout.addWidget(self.search)

        self.results = QListWidget()
        self.results.setObjectName("QuickResults")
        self.results.itemActivated.connect(lambda _: self._choose_selected())
        layout.addWidget(self.results, 1)

        hint = QLabel("Enter to open  ·  Esc to close")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self._update_results("")
        self.search.setFocus()

    def _update_results(self, query: str) -> None:
        self.results.clear()
        for destination in search_navigation(self.destinations, query):
            item = QListWidgetItem(f"{destination.name}     ·     {destination.section}")
            item.setData(Qt.ItemDataRole.UserRole, destination.index)
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def _choose_selected(self) -> None:
        item = self.results.currentItem()
        if item is None:
            return
        self.selected_index = int(item.data(Qt.ItemDataRole.UserRole))
        self.accept()
