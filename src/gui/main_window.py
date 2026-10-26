"""Main window for py-qr desktop application."""

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
)

from src.core.history import HistoryManager
from src.core.parser import EmailConfig, VCardConfig, WifiConfig
from src.gui.tabs.generator_tab import GeneratorTab
from src.gui.tabs.history_tab import HistoryTab
from src.gui.tabs.reader_tab import ReaderTab
from src.gui.theme import apply_theme, detect_system_theme


class MainWindow(QMainWindow):
    """The central application window with tabs, menus, and persistence."""

    def __init__(self, history_manager: HistoryManager | None = None):
        super().__init__()
        self.setWindowTitle("py-qr — QR-Code Studio & Reader")
        self.setMinimumSize(700, 550)
        self.resize(850, 650)

        self.settings = QSettings("TGBox", "py-qr")
        self.history_manager = history_manager or HistoryManager()

        self._setup_ui()
        self._setup_menus()
        self._restore_settings()

    def _setup_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self.generator_tab = GeneratorTab(self.history_manager)
        self.generator_tab.status_message.connect(self.status_bar_message)
        self.tabs.addTab(self.generator_tab, "⚡ Generieren")

        self.reader_tab = ReaderTab(self.history_manager)
        self.reader_tab.status_message.connect(self.status_bar_message)
        self.reader_tab.request_load_wifi.connect(self._transfer_wifi_to_generator)
        self.reader_tab.request_load_vcard.connect(self._transfer_vcard_to_generator)
        self.reader_tab.request_load_email.connect(self._transfer_email_to_generator)
        self.tabs.addTab(self.reader_tab, "🔍 Lesen")

        self.history_tab = HistoryTab(self.history_manager)
        self.history_tab.status_message.connect(self.status_bar_message)
        self.tabs.addTab(self.history_tab, "📜 Verlauf")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit", 3000)

    def status_bar_message(self, message: str, timeout: int = 3000) -> None:
        """Display message on status bar."""
        self.status_bar.showMessage(message, timeout)

    def _transfer_wifi_to_generator(self, config: WifiConfig) -> None:
        """Load scanned WiFi config into Generator tab and switch to it."""
        self.generator_tab.load_wifi_data(config)
        self.tabs.setCurrentIndex(0)
        self.status_bar_message(f"WLAN '{config.ssid}' in Generator geladen", 3000)

    def _transfer_vcard_to_generator(self, config: VCardConfig) -> None:
        """Load scanned vCard config into Generator tab and switch to it."""
        self.generator_tab.load_vcard_data(config)
        self.tabs.setCurrentIndex(0)
        name = f"{config.first_name} {config.last_name}".strip()
        self.status_bar_message(f"Kontakt '{name or 'vCard'}' in Generator geladen", 3000)

    def _transfer_email_to_generator(self, config: EmailConfig) -> None:
        """Load scanned Email config into Generator tab and switch to it."""
        self.generator_tab.load_email_data(config)
        self.tabs.setCurrentIndex(0)
        self.status_bar_message(f"E-Mail an '{config.to}' in Generator geladen", 3000)

    def _setup_menus(self) -> None:
        menubar = self.menuBar()

        # Menu: Datei
        file_menu = menubar.addMenu("&Datei")

        batch_action = QAction("&Stapelverarbeitung...", self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.setStatusTip(
            "Mehrere QR-Codes aus CSV/Liste erstellen und als ZIP oder PDF exportieren"
        )
        batch_action.triggered.connect(self._open_batch_dialog)
        file_menu.addAction(batch_action)

        file_menu.addSeparator()

        exit_action = QAction("&Beenden", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Anwendung beenden")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu: Ansicht
        view_menu = menubar.addMenu("&Ansicht")

        self.fullscreen_action = QAction("&Vollbild umschalten", self)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.setStatusTip("Zwischen Vollbild und Fenstermodus wechseln (F11)")
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

        view_menu.addSeparator()

        self.theme_action = QAction("&Theme wechseln (Dunkel / Hell)", self)
        self.theme_action.setStatusTip("Zwischen dunklem und hellem Farbschema umschalten")
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)

        # Menu: Hilfe
        help_menu = menubar.addMenu("&Hilfe")
        about_action = QAction("&Über py-qr", self)
        about_action.setStatusTip("Informationen über diese Anwendung")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.status_bar.showMessage("Fenstermodus aktiviert", 2000)
        else:
            self.showFullScreen()
            self.status_bar.showMessage("Vollbildmodus aktiviert (F11 zum Beenden)", 3000)

    def toggle_theme(self) -> None:
        """Toggle between Dark and Light mode and save preference."""
        current_theme = self.settings.value("theme", detect_system_theme())
        new_theme = "light" if current_theme == "dark" else "dark"
        self.set_theme(new_theme)

    def set_theme(self, theme_name: str) -> None:
        """Apply a specific theme and store it in QSettings."""
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_name)
        self.settings.setValue("theme", theme_name)
        theme_display = "Dunkel" if theme_name == "dark" else "Hell"
        self.status_bar.showMessage(f"Farbschema gewechselt: {theme_display}", 2000)

    def _open_batch_dialog(self) -> None:
        """Open the batch QR processing studio dialog."""
        self.generator_tab.open_batch_studio()

    def _show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "Über py-qr",
            "<h3>py-qr — QR-Code Studio & Reader</h3>"
            "<p>Ein leichtgewichtiges Desktop-Werkzeug zum schnellen Erstellen und "
            "Lesen von QR-Codes ohne Online-Dienste.</p>"
            "<p><b>Version:</b> 0.2.0<br>"
            "<b>Tastenkürzel:</b><br>"
            "- <code>F11</code>: Vollbild umschalten<br>"
            "- <code>Strg+B</code>: Stapelverarbeitung (Batch-Studio)<br>"
            "- <code>Strg+V</code>: QR-Code aus Zwischenablage dekodieren<br>"
            "- <code>Strg+Q</code>: Beenden</p>",
        )

    def _restore_settings(self) -> None:
        """Restore window size, position, and theme from QSettings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        saved_theme = self.settings.value("theme")
        if not saved_theme:
            saved_theme = detect_system_theme()
        self.set_theme(saved_theme)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save window settings when closing."""
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
