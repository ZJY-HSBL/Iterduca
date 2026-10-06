from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iterduca.services.profile_service import ProfileInfo


class ProfilesPage(QWidget):
    import_requested = pyqtSignal(str)
    active_profile_changed = pyqtSignal(str)
    subscription_add_requested = pyqtSignal(str)
    subscription_update_requested = pyqtSignal(str)
    subscription_update_all_requested = pyqtSignal()
    delete_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Profiles")
        title.setObjectName("Title")
        layout.addWidget(title)

        hint = QLabel(
            "Imported profiles are preserved unchanged; "
            "Iterduca creates a disposable runtime config."
        )
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        subscription_row = QHBoxLayout()
        self.subscription_url = QLineEdit()
        self.subscription_url.setPlaceholderText("https://example.com/subscription")
        add_subscription = QPushButton("Add subscription")
        add_subscription.clicked.connect(self._add_subscription)
        subscription_row.addWidget(self.subscription_url, 1)
        subscription_row.addWidget(add_subscription)
        layout.addLayout(subscription_row)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.import_button = QPushButton("Import YAML")
        self.update_button = QPushButton("Update subscription")
        self.update_all_button = QPushButton("Update all")
        self.delete_button = QPushButton("Delete selected")
        self.delete_button.setObjectName("DangerButton")
        self.use_button = QPushButton("Use selected")
        self.use_button.setObjectName("PrimaryButton")
        actions.addWidget(self.import_button)
        actions.addWidget(self.update_button)
        actions.addWidget(self.update_all_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.use_button)
        layout.addLayout(actions)

        self.import_button.clicked.connect(self._pick_file)
        self.update_button.clicked.connect(self._update_subscription)
        self.update_all_button.clicked.connect(self.subscription_update_all_requested.emit)
        self.delete_button.clicked.connect(self._delete_selected)
        self.use_button.clicked.connect(self._activate)
        self._profiles: list[ProfileInfo] = []
        self._subscription_names: set[str] = set()

    def set_profiles(
        self,
        profiles: list[ProfileInfo],
        active: str,
        subscription_names: set[str] | None = None,
    ) -> None:
        self._profiles = profiles
        self._subscription_names = subscription_names or set()
        self.list.clear()
        active_row = -1

        for index, profile in enumerate(profiles):
            parts = [profile.name, f"{profile.proxy_count} proxies"]
            if profile.name in self._subscription_names:
                parts.append("SUBSCRIPTION")
            if profile.name == active:
                parts.append("ACTIVE")
                active_row = index
            self.list.addItem("    ".join(parts))

        if active_row >= 0:
            self.list.setCurrentRow(active_row)

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import profile", "", "YAML (*.yaml *.yml)")
        if path:
            self.import_requested.emit(path)

    def _activate(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._profiles):
            self.active_profile_changed.emit(self._profiles[row].name)

    def _add_subscription(self) -> None:
        url = self.subscription_url.text().strip()
        if url:
            self.subscription_add_requested.emit(url)

    def _update_subscription(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._profiles):
            self.subscription_update_requested.emit(self._profiles[row].name)


    def _delete_selected(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._profiles):
            self.delete_requested.emit(self._profiles[row].name)
