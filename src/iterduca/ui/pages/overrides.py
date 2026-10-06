from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OverridesPage(QWidget):
    save_requested = pyqtSignal(str)
    reload_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Overrides")
        title.setObjectName("Title")
        layout.addWidget(title)

        hint = QLabel(
            "YAML overrides are deep-merged into the active profile at runtime. "
            "Iterduca still owns the local Controller address, secret, mode, and mixed port."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "dns:\n"
            "  enable: true\n"
            "tcp-concurrent: true\n"
            "unified-delay: true\n"
        )
        layout.addWidget(self.editor, 1)

        reload_button = QPushButton("Reload")
        save_button = QPushButton("Save overrides")
        save_button.setObjectName("PrimaryButton")
        reload_button.clicked.connect(self.reload_requested.emit)
        save_button.clicked.connect(lambda: self.save_requested.emit(self.editor.toPlainText()))
        layout.addWidget(reload_button)
        layout.addWidget(save_button)

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)
