"""Theme system with Dark and Light stylesheets and system detection."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0f172a;
    color: #f8fafc;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #f8fafc;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background: #334155;
    color: #f1f5f9;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #60a5fa;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#secondaryButton {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
}

QPushButton#secondaryButton:hover {
    background-color: #475569;
}

QPushButton#dangerButton {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    color: #f8fafc;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Labels */
QLabel {
    color: #f8fafc;
}

QLabel#mutedLabel {
    color: #94a3b8;
    font-size: 12px;
}

/* Dropzone */
QFrame#dropZone {
    background-color: #1e293b;
    border: 2px dashed #475569;
    border-radius: 12px;
}

QFrame#dropZone:hover {
    border-color: #3b82f6;
    background-color: #1e293b;
}

/* Lists and Tables */
QListWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 2px;
    border-bottom: 1px solid #283548;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #334155;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f8fafc;
    color: #0f172a;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #0f172a;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #e2e8f0;
    color: #64748b;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background: #cbd5e1;
    color: #0f172a;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #2563eb;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton#secondaryButton {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
}

QPushButton#secondaryButton:hover {
    background-color: #e2e8f0;
}

QPushButton#dangerButton {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    color: #0f172a;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Labels */
QLabel {
    color: #0f172a;
}

QLabel#mutedLabel {
    color: #64748b;
    font-size: 12px;
}

/* Dropzone */
QFrame#dropZone {
    background-color: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
}

QFrame#dropZone:hover {
    border-color: #2563eb;
    background-color: #eff6ff;
}

/* Lists and Tables */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 2px;
    border-bottom: 1px solid #f1f5f9;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f1f5f9;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #f8fafc;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def detect_system_theme() -> str:
    """Detect whether Windows system is currently in Dark or Light mode."""
    app = QApplication.instance()
    if app and hasattr(app, "styleHints"):
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
        if scheme == Qt.ColorScheme.Light:
            return "light"
    return "dark"  # Default fallback


def get_theme_stylesheet(theme_name: str) -> str:
    """Return the QSS stylesheet for given theme name."""
    if theme_name.lower() == "light":
        return LIGHT_STYLESHEET
    return DARK_STYLESHEET


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Apply theme stylesheet to QApplication."""
    stylesheet = get_theme_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
