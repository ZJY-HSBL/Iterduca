APP_STYLESHEET = """
QWidget {
    background: #0b0d11;
    color: #e8ebf2;
    font-family: "Segoe UI";
    font-size: 13px;
}
QMainWindow, QStackedWidget { background: #0b0d11; }

#Sidebar {
    background: #11141a;
    border-right: 1px solid #202631;
}
#Brand {
    color: #f7f8fb;
    font-size: 23px;
    font-weight: 700;
    padding: 4px 8px 0 8px;
}
#BrandSub {
    color: #667085;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 0 8px 10px 8px;
}
#NavSection {
    color: #626b7d;
    font-size: 10px;
    font-weight: 700;
    padding: 11px 10px 3px 10px;
}
#NavButton {
    color: #aeb5c3;
    background: transparent;
    border: 0;
    border-left: 3px solid transparent;
    border-radius: 7px;
    padding: 8px 10px;
    text-align: left;
    min-height: 18px;
}
#NavButton:hover {
    color: #f4f6fa;
    background: #171c24;
}
#NavButton:checked {
    color: #f7f8fb;
    background: #1b2230;
    border-left: 3px solid #8aa4ff;
    font-weight: 600;
}

QPushButton {
    color: #dbe0e9;
    background: #161a21;
    border: 1px solid #2a303c;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover {
    background: #1d222c;
    border-color: #353d4c;
}
QPushButton:pressed { background: #141820; }
QPushButton:disabled {
    color: #5f6674;
    background: #12151a;
    border-color: #1d222b;
}
QPushButton#PrimaryButton {
    background: #dfe6ff;
    color: #11151e;
    border-color: #dfe6ff;
    text-align: center;
    font-weight: 650;
}
QPushButton#PrimaryButton:hover { background: #eef2ff; }
QPushButton#DangerButton {
    background: #2a171d;
    color: #ffb5c0;
    border-color: #4a242d;
    text-align: center;
}
QPushButton#DangerButton:hover { background: #351b23; }

QFrame#Card {
    background: #12161d;
    border: 1px solid #242b36;
    border-radius: 12px;
}
QLabel#Title {
    color: #f6f7fa;
    font-size: 26px;
    font-weight: 700;
}
QLabel#Metric {
    color: #f5f7fb;
    font-size: 26px;
    font-weight: 700;
}
QLabel#Muted { color: #7f8898; }

QLineEdit, QComboBox, QListWidget, QPlainTextEdit, QSpinBox {
    background: #0f1319;
    border: 1px solid #29313d;
    border-radius: 8px;
    padding: 7px 9px;
    selection-background-color: #31415e;
}
QLineEdit:focus, QComboBox:focus, QListWidget:focus,
QPlainTextEdit:focus, QSpinBox:focus {
    border-color: #647fb3;
}
QComboBox::drop-down {
    border: 0;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #12161d;
    color: #e8ebf2;
    border: 1px solid #2a303c;
    selection-background-color: #27334a;
}
QListWidget::item {
    padding: 8px 9px;
    border-radius: 6px;
}
QListWidget::item:hover { background: #171d26; }
QListWidget::item:selected { background: #263249; }

QTableWidget, QTableView {
    background: #0f1319;
    alternate-background-color: #11161d;
    border: 1px solid #29313d;
    border-radius: 8px;
    gridline-color: #1c222b;
    selection-background-color: #263249;
    selection-color: #f5f7fb;
}
QHeaderView::section {
    color: #929baa;
    background: #12171e;
    border: 0;
    border-bottom: 1px solid #29313d;
    padding: 8px 9px;
    font-weight: 600;
}
QTableCornerButton::section {
    background: #12171e;
    border: 0;
}

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QProgressBar {
    background: #0f1319;
    border: 1px solid #29313d;
    border-radius: 6px;
    text-align: center;
    min-height: 16px;
}
QProgressBar::chunk {
    background: #8099df;
    border-radius: 5px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #313947;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #313947;
    min-width: 30px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QToolTip {
    color: #edf0f6;
    background: #181d25;
    border: 1px solid #303846;
    padding: 5px;
}
"""