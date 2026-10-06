from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iterduca.services.profile_service import ProfileInfo


class ProfilesPage(QWidget):
    import_requested = pyqtSignal(str)
    active_profile_changed = pyqtSignal(str)

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
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.import_button = QPushButton("Import YAML")
        self.use_button = QPushButton("Use selected")
        self.use_button.setObjectName("PrimaryButton")
        actions.addWidget(self.import_button)
        actions.addWidget(self.use_button)
        layout.addLayout(actions)

        self.import_button.clicked.connect(self._pick_file)
        self.use_button.clicked.connect(self._activate)
        self._profiles: list[ProfileInfo] = []

    def set_profiles(self, profiles: list[ProfileInfo], active: str) -> None:
        self._profiles = profiles
        self.list.clear()
        active_row = -1
        for index, profile in enumerate(profiles):
            label = f"{profile.name}    {profile.proxy_count} proxies"
            if profile.name == active:
                label += "    ACTIVE"
                active_row = index
            self.list.addItem(label)
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
