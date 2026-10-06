from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LogsPage(QWidget):
    export_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("Logs")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(2000)
        layout.addWidget(self.output, 1)

        actions = QHBoxLayout()
        export = QPushButton("Export logs")
        clear = QPushButton("Clear logs")
        export.clicked.connect(self.export_requested.emit)
        clear.clicked.connect(self._clear)
        actions.addWidget(export)
        actions.addWidget(clear)
        actions.addStretch(1)
        layout.addLayout(actions)

    def append(self, message: str) -> None:
        self.output.appendPlainText(message)

    def _clear(self) -> None:
        self.output.clear()
        self.clear_requested.emit()
