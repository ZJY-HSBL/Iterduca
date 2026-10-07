from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
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
from iterduca.services.subscription_service import SubscriptionInfo


class ProfilesPage(QWidget):
    import_requested = pyqtSignal(str)
    active_profile_changed = pyqtSignal(str)
    subscription_add_requested = pyqtSignal(str)
    subscription_update_requested = pyqtSignal(str)
    subscription_update_all_requested = pyqtSignal()
    delete_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Profiles")
        title.setObjectName("Title")
        layout.addWidget(title)

        hint = QLabel(
            "Imported profiles are preserved unchanged. Drop .yaml/.yml files anywhere "
            "on this page to import them."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
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
        self.list.currentRowChanged.connect(self._show_details)
        layout.addWidget(self.list, 1)

        self.details = QLabel("Select a Profile to view statistics.")
        self.details.setObjectName("Muted")
        self.details.setWordWrap(True)
        layout.addWidget(self.details)

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
        self._subscriptions: dict[str, SubscriptionInfo] = {}

    def set_profiles(
        self,
        profiles: list[ProfileInfo],
        active: str,
        subscriptions: dict[str, SubscriptionInfo] | None = None,
    ) -> None:
        self._profiles = profiles
        self._subscriptions = subscriptions or {}
        self.list.clear()
        active_row = -1

        for index, profile in enumerate(profiles):
            parts = [
                profile.name,
                f"{profile.proxy_count} proxies",
                f"{profile.rule_count} rules",
            ]
            subscription = self._subscriptions.get(profile.name)
            if subscription is not None:
                parts.append("SUBSCRIPTION")
                if subscription.total_bytes > 0:
                    parts.append(
                        f"{self._format_size(subscription.used_bytes)} / "
                        f"{self._format_size(subscription.total_bytes)}"
                    )
                if self._expires_soon(subscription):
                    parts.append("EXPIRES SOON")
            if profile.name == active:
                parts.append("ACTIVE")
                active_row = index
            self.list.addItem("    ".join(parts))

        if active_row >= 0:
            self.list.setCurrentRow(active_row)
        elif profiles:
            self.list.setCurrentRow(0)
        else:
            self.details.setText("No Profiles imported.")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt API
        if self._yaml_paths(event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt API
        paths = self._yaml_paths(event.mimeData().urls())
        if not paths:
            return
        for path in paths:
            self.import_requested.emit(str(path))
        event.acceptProposedAction()

    def _show_details(self) -> None:
        row = self.list.currentRow()
        if not 0 <= row < len(self._profiles):
            self.details.setText("Select a Profile to view statistics.")
            return

        profile = self._profiles[row]
        subscription = self._subscriptions.get(profile.name)
        parts = [
            f"Nodes {profile.proxy_count}",
            f"Groups {profile.group_count}",
            f"Rules {profile.rule_count}",
            f"Proxy Providers {profile.proxy_provider_count}",
            f"Rule Providers {profile.rule_provider_count}",
            f"Size {self._format_size(profile.size_bytes)}",
        ]
        if subscription is not None:
            parts.append(f"Subscription updated {subscription.updated_at}")
            if subscription.total_bytes > 0:
                parts.append(
                    f"Used {self._format_size(subscription.used_bytes)} / "
                    f"{self._format_size(subscription.total_bytes)}"
                )
                parts.append(
                    f"Remaining {self._format_size(subscription.remaining_bytes)}"
                )
            if subscription.expire_at > 0:
                expiry = datetime.fromtimestamp(subscription.expire_at).astimezone()
                parts.append(f"Expires {expiry:%Y-%m-%d %H:%M}")
        self.details.setText("  ·  ".join(parts))

    def _pick_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Profiles",
            "",
            "YAML (*.yaml *.yml)",
        )
        for path in paths:
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

    @staticmethod
    def _yaml_paths(urls) -> list[Path]:
        paths: list[Path] = []
        for url in urls:
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
                paths.append(path)
        return paths

    @staticmethod
    def _format_size(value: int) -> str:
        size = float(max(0, value))
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
            size /= 1024
        return "0 B"

    @staticmethod
    def _expires_soon(subscription: SubscriptionInfo) -> bool:
        if subscription.expire_at <= 0:
            return False
        seconds_left = subscription.expire_at - int(datetime.now().timestamp())
        return 0 <= seconds_left <= 7 * 24 * 60 * 60
