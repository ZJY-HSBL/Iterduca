from PyQt6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class LogsPage(QWidget):
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
        clear = QPushButton("Clear")
        clear.clicked.connect(self.output.clear)
        layout.addWidget(clear)

    def append(self, message: str) -> None:
        self.output.appendPlainText(message)
