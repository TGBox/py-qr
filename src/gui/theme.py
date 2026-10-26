"""Theme system with Dark and Light stylesheets, custom palettes, and system detection."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

DARK_STYLESHEET = """
QMainWindow, QDialog, QMessageBox {
    background-color: #0f172a;
    color: #f8fafc;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    color: #f8fafc;
}

/* Menu Bar */
QMenuBar {
    background-color: #0f172a;
    color: #f8fafc;
    border-bottom: 1px solid #1e293b;
    padding: 2px 4px;
    font-weight: 500;
}

QMenuBar::item {
    background-color: transparent;
    color: #f8fafc;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #1e293b;
    color: #60a5fa;
}

QMenuBar::item:pressed {
    background-color: #334155;
    color: #ffffff;
}

/* Menus */
QMenu {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    background-color: transparent;
    color: #f8fafc;
    padding: 7px 24px 7px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #64748b;
}

QMenu::separator {
    height: 1px;
    background-color: #334155;
    margin: 4px 6px;
}

/* Status Bar */
QStatusBar {
    background-color: #0f172a;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 9pt;
}

QStatusBar::item {
    border: none;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 8px;
    top: -1px;
}

QTabBar {
    background: transparent;
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
    font-size: 10pt;
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

/* Inputs & Form Elements */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    color: #f8fafc;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QLineEdit:read-only, QTextEdit:read-only, QPlainTextEdit:read-only {
    background-color: #162032;
    color: #cbd5e1;
    border: 1px solid #334155;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    color: #f8fafc;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #334155;
    color: #ffffff;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Radio buttons & Checkboxes */
QRadioButton, QCheckBox {
    color: #f8fafc;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #475569;
    background-color: #0f172a;
}

QRadioButton::indicator:checked {
    border-color: #2563eb;
    background-color: #2563eb;
}

QRadioButton::indicator:hover {
    border-color: #3b82f6;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #475569;
    background-color: #0f172a;
}

QCheckBox::indicator:checked {
    border-color: #2563eb;
    background-color: #2563eb;
}

QCheckBox::indicator:hover {
    border-color: #3b82f6;
}

/* Labels */
QLabel {
    color: #f8fafc;
}

QLabel#mutedLabel {
    color: #94a3b8;
    font-size: 9pt;
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
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    color: #f8fafc;
    background-color: transparent;
    border-radius: 6px;
    padding: 9px 12px;
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

/* ToolTips */
QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 9pt;
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

QScrollBar:horizontal {
    border: none;
    background: #0f172a;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tables */
QTableWidget {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #334155;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #334155;
}

QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #334155;
    font-weight: 600;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog, QMessageBox {
    background-color: #f8fafc;
    color: #0f172a;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    color: #0f172a;
}

/* Menu Bar */
QMenuBar {
    background-color: #f8fafc;
    color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 4px;
    font-weight: 500;
}

QMenuBar::item {
    background-color: transparent;
    color: #0f172a;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #e2e8f0;
    color: #1d4ed8;
}

QMenuBar::item:pressed {
    background-color: #cbd5e1;
    color: #1d4ed8;
}

/* Menus */
QMenu {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    background-color: transparent;
    color: #0f172a;
    padding: 7px 24px 7px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #94a3b8;
}

QMenu::separator {
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 6px;
}

/* Status Bar */
QStatusBar {
    background-color: #f8fafc;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    font-size: 9pt;
}

QStatusBar::item {
    border: none;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar {
    background: transparent;
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
    font-size: 10pt;
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
    border-color: #94a3b8;
}

QPushButton#dangerButton {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

/* Inputs & Form Elements */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

QLineEdit:read-only, QTextEdit:read-only, QPlainTextEdit:read-only {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #e2e8f0;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    color: #0f172a;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Radio buttons & Checkboxes */
QRadioButton, QCheckBox {
    color: #0f172a;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #cbd5e1;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    border-color: #2563eb;
    background-color: #2563eb;
}

QRadioButton::indicator:hover {
    border-color: #2563eb;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    border-color: #2563eb;
    background-color: #2563eb;
}

QCheckBox::indicator:hover {
    border-color: #2563eb;
}

/* Labels */
QLabel {
    color: #0f172a;
}

QLabel#mutedLabel {
    color: #64748b;
    font-size: 9pt;
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
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    color: #0f172a;
    background-color: transparent;
    border-radius: 6px;
    padding: 9px 12px;
    margin-bottom: 2px;
    border-bottom: 1px solid #f1f5f9;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f1f5f9;
    color: #0f172a;
}

/* ToolTips */
QToolTip {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 9pt;
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

QScrollBar:horizontal {
    border: none;
    background: #f8fafc;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    gridline-color: #e2e8f0;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #f1f5f9;
}

QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #475569;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #cbd5e1;
    font-weight: 600;
}
"""


def create_light_palette() -> QPalette:
    """Create a complete Qt palette for light mode."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#94a3b8"))
    return palette


def create_dark_palette() -> QPalette:
    """Create a complete Qt palette for dark mode."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e293b"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0f172a"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e293b"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1e293b"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#3b82f6"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
    return palette


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
    """Apply theme stylesheet and matching Qt palette to QApplication."""
    is_light = theme_name.lower() == "light"
    palette = create_light_palette() if is_light else create_dark_palette()
    app.setPalette(palette)
    stylesheet = get_theme_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
