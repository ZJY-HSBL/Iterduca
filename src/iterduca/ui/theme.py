APP_STYLESHEET = """
QWidget {
    background: #0f1115;
    color: #e7e9ee;
    font-family: "Segoe UI";
    font-size: 13px;
}
QMainWindow, QStackedWidget { background: #0f1115; }
#Sidebar { background: #151820; border-right: 1px solid #242936; }
#Brand { font-size: 20px; font-weight: 700; padding: 12px 8px; }
QPushButton {
    background: transparent;
    border: 0;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
}
QPushButton:hover { background: #202531; }
QPushButton:checked { background: #2a3140; font-weight: 600; }
QPushButton#PrimaryButton {
    background: #e7e9ee;
    color: #0f1115;
    text-align: center;
    font-weight: 600;
}
QPushButton#DangerButton {
    background: #321c22;
    color: #ffbec8;
    text-align: center;
}
QFrame#Card {
    background: #171a21;
    border: 1px solid #272c38;
    border-radius: 12px;
}
QLabel#Title { font-size: 24px; font-weight: 700; }
QLabel#Metric { font-size: 28px; font-weight: 700; }
QLabel#Muted { color: #8f97a7; }
QLineEdit, QComboBox, QListWidget, QPlainTextEdit, QSpinBox {
    background: #11141a;
    border: 1px solid #2a303d;
    border-radius: 7px;
    padding: 7px;
}
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background: #293141; }
QCheckBox { spacing: 8px; }
"""
