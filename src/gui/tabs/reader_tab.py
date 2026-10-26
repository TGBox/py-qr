"""Reader tab for decoding QR codes from files, drag & drop, and clipboard."""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.history import HistoryManager
from src.core.parser import (
    PayloadType,
    ScanResult,
    format_email_payload,
)
from src.gui.workers import DecodeWorker


class DropZoneFrame(QFrame):
    """Custom frame supporting drag and drop of image files."""

    file_dropped = Signal(Path)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                suffix = Path(url.toLocalFile()).suffix.lower()
                if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self.file_dropped.emit(path)
                event.acceptProposedAction()
                return


class ReaderTab(QWidget):
    """Tab widget for decoding QR codes with smart parsing and quick actions."""

    status_message = Signal(str, int)
    request_load_wifi = Signal(object)  # WifiConfig
    request_load_vcard = Signal(object)  # VCardConfig
    request_load_email = Signal(object)  # EmailConfig

    def __init__(self, history_manager: HistoryManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.active_worker: DecodeWorker | None = None
        self.last_result: ScanResult | None = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        # Drop Zone Header
        self.drop_zone = DropZoneFrame()
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setContentsMargins(24, 28, 24, 28)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(10)

        drop_icon = QLabel("📥")
        drop_icon.setStyleSheet("font-size: 38px;")
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_icon)

        drop_title = QLabel("QR-Code Bild hier hineinziehen")
        drop_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        drop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_title)

        drop_subtitle = QLabel(
            "Unterstützt PNG, JPG, WEBP, BMP oder direkt <b>Strg+V</b> zum Einfügen aus der Zwischenablage"
        )
        drop_subtitle.setObjectName("mutedLabel")
        drop_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_subtitle)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(12)

        self.btn_select_file = QPushButton("📁 Bilddatei auswählen...")
        self.btn_select_file.setObjectName("secondaryButton")
        btn_row.addWidget(self.btn_select_file)

        self.btn_paste_clipboard = QPushButton("📋 Aus Zwischenablage (Strg+V)")
        btn_row.addWidget(self.btn_paste_clipboard)

        drop_layout.addLayout(btn_row)
        layout.addWidget(self.drop_zone)

        # Status & Loading Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("mutedLabel")
        layout.addWidget(self.status_label)

        # Result Display (Stacked Widget)
        self.result_group = QGroupBox("Ergebnis")
        result_group_layout = QVBoxLayout(self.result_group)
        result_group_layout.setSpacing(12)

        self.result_stack = QStackedWidget()

        # Page 0: Empty placeholder
        empty_page = QLabel("Noch kein QR-Code gescannt.")
        empty_page.setObjectName("mutedLabel")
        empty_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_stack.addWidget(empty_page)

        # Page 1: URL Result
        url_page = QWidget()
        url_layout = QVBoxLayout(url_page)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(10)

        url_badge = QLabel("🌐 Webadresse (URL)")
        url_badge.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 14px;")
        url_layout.addWidget(url_badge)

        self.url_display = QPlainTextEdit()
        self.url_display.setReadOnly(True)
        self.url_display.setMaximumHeight(70)
        url_layout.addWidget(self.url_display)

        url_btn_row = QHBoxLayout()
        self.btn_open_browser = QPushButton("🚀 Im Browser öffnen")
        self.btn_copy_url = QPushButton("📋 Link kopieren")
        self.btn_copy_url.setObjectName("secondaryButton")
        url_btn_row.addWidget(self.btn_open_browser)
        url_btn_row.addWidget(self.btn_copy_url)
        url_btn_row.addStretch()
        url_layout.addLayout(url_btn_row)
        self.result_stack.addWidget(url_page)

        # Page 2: WiFi Result
        wifi_page = QWidget()
        wifi_layout = QVBoxLayout(wifi_page)
        wifi_layout.setContentsMargins(0, 0, 0, 0)
        wifi_layout.setSpacing(10)

        wifi_badge = QLabel("📶 WLAN-Zugangsdaten")
        wifi_badge.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        wifi_layout.addWidget(wifi_badge)

        self.wifi_details_label = QLabel()
        self.wifi_details_label.setTextFormat(Qt.TextFormat.RichText)
        self.wifi_details_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        wifi_layout.addWidget(self.wifi_details_label)

        wifi_btn_row = QHBoxLayout()
        self.btn_copy_wifi_pass = QPushButton("🔑 Passwort kopieren")
        self.btn_copy_wifi_ssid = QPushButton("📋 SSID kopieren")
        self.btn_copy_wifi_ssid.setObjectName("secondaryButton")
        self.btn_transfer_wifi = QPushButton("⚡ In Generator laden")
        self.btn_transfer_wifi.setObjectName("secondaryButton")

        wifi_btn_row.addWidget(self.btn_copy_wifi_pass)
        wifi_btn_row.addWidget(self.btn_copy_wifi_ssid)
        wifi_btn_row.addWidget(self.btn_transfer_wifi)
        wifi_btn_row.addStretch()
        wifi_layout.addLayout(wifi_btn_row)
        self.result_stack.addWidget(wifi_page)

        # Page 3: Plain text Result
        text_page = QWidget()
        text_layout = QVBoxLayout(text_page)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(10)

        text_badge = QLabel("📝 Textinhalt")
        text_badge.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
        text_layout.addWidget(text_badge)

        self.text_display = QPlainTextEdit()
        self.text_display.setReadOnly(True)
        text_layout.addWidget(self.text_display)

        text_btn_row = QHBoxLayout()
        self.btn_copy_text = QPushButton("📋 Text kopieren")
        text_btn_row.addWidget(self.btn_copy_text)
        text_btn_row.addStretch()
        text_layout.addLayout(text_btn_row)
        self.result_stack.addWidget(text_page)

        # Page 4: vCard Result
        vcard_page = QWidget()
        vcard_layout = QVBoxLayout(vcard_page)
        vcard_layout.setContentsMargins(0, 0, 0, 0)
        vcard_layout.setSpacing(10)

        vcard_badge = QLabel("👤 Visitenkarte (vCard)")
        vcard_badge.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 14px;")
        vcard_layout.addWidget(vcard_badge)

        self.vcard_details_label = QLabel()
        self.vcard_details_label.setTextFormat(Qt.TextFormat.RichText)
        self.vcard_details_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        vcard_layout.addWidget(self.vcard_details_label)

        vcard_btn_row = QHBoxLayout()
        self.btn_save_vcf = QPushButton("💾 Als Kontakt (.vcf) speichern")
        self.btn_copy_vcard_phone = QPushButton("📞 Telefon kopieren")
        self.btn_copy_vcard_phone.setObjectName("secondaryButton")
        self.btn_copy_vcard_email = QPushButton("✉️ E-Mail kopieren")
        self.btn_copy_vcard_email.setObjectName("secondaryButton")
        self.btn_transfer_vcard = QPushButton("⚡ In Generator laden")
        self.btn_transfer_vcard.setObjectName("secondaryButton")

        vcard_btn_row.addWidget(self.btn_save_vcf)
        vcard_btn_row.addWidget(self.btn_copy_vcard_phone)
        vcard_btn_row.addWidget(self.btn_copy_vcard_email)
        vcard_btn_row.addWidget(self.btn_transfer_vcard)
        vcard_btn_row.addStretch()
        vcard_layout.addLayout(vcard_btn_row)
        self.result_stack.addWidget(vcard_page)

        # Page 5: Email Result
        email_page = QWidget()
        email_layout = QVBoxLayout(email_page)
        email_layout.setContentsMargins(0, 0, 0, 0)
        email_layout.setSpacing(10)

        email_badge = QLabel("✉️ E-Mail Entwurf")
        email_badge.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 14px;")
        email_layout.addWidget(email_badge)

        self.email_details_label = QLabel()
        self.email_details_label.setTextFormat(Qt.TextFormat.RichText)
        self.email_details_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        email_layout.addWidget(self.email_details_label)

        email_btn_row = QHBoxLayout()
        self.btn_open_email = QPushButton("🚀 E-Mail schreiben")
        self.btn_copy_email_addr = QPushButton("📋 Adresse kopieren")
        self.btn_copy_email_addr.setObjectName("secondaryButton")
        self.btn_transfer_email = QPushButton("⚡ In Generator laden")
        self.btn_transfer_email.setObjectName("secondaryButton")

        email_btn_row.addWidget(self.btn_open_email)
        email_btn_row.addWidget(self.btn_copy_email_addr)
        email_btn_row.addWidget(self.btn_transfer_email)
        email_btn_row.addStretch()
        email_layout.addLayout(email_btn_row)
        self.result_stack.addWidget(email_page)

        # Page 6: Geo Result
        geo_page = QWidget()
        geo_layout = QVBoxLayout(geo_page)
        geo_layout.setContentsMargins(0, 0, 0, 0)
        geo_layout.setSpacing(10)

        geo_badge = QLabel("📍 Standort / Koordinaten")
        geo_badge.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
        geo_layout.addWidget(geo_badge)

        self.geo_details_label = QLabel()
        self.geo_details_label.setTextFormat(Qt.TextFormat.RichText)
        self.geo_details_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        geo_layout.addWidget(self.geo_details_label)

        geo_btn_row = QHBoxLayout()
        self.btn_open_maps = QPushButton("🗺️ In Google Maps öffnen")
        self.btn_copy_coords = QPushButton("📋 Koordinaten kopieren")
        self.btn_copy_coords.setObjectName("secondaryButton")

        geo_btn_row.addWidget(self.btn_open_maps)
        geo_btn_row.addWidget(self.btn_copy_coords)
        geo_btn_row.addStretch()
        geo_layout.addLayout(geo_btn_row)
        self.result_stack.addWidget(geo_page)

        result_group_layout.addWidget(self.result_stack)
        layout.addWidget(self.result_group, stretch=1)

    def _connect_signals(self) -> None:
        self.drop_zone.file_dropped.connect(self.decode_from_path)
        self.btn_select_file.clicked.connect(self._choose_file)
        self.btn_paste_clipboard.clicked.connect(self.decode_from_clipboard)

        self.btn_open_browser.clicked.connect(self._open_url_in_browser)
        self.btn_copy_url.clicked.connect(self._copy_url)

        self.btn_copy_wifi_pass.clicked.connect(self._copy_wifi_password)
        self.btn_copy_wifi_ssid.clicked.connect(self._copy_wifi_ssid)
        self.btn_transfer_wifi.clicked.connect(self._transfer_wifi_to_generator)

        self.btn_save_vcf.clicked.connect(self._save_vcf)
        self.btn_copy_vcard_phone.clicked.connect(self._copy_vcard_phone)
        self.btn_copy_vcard_email.clicked.connect(self._copy_vcard_email)
        self.btn_transfer_vcard.clicked.connect(self._transfer_vcard_to_generator)

        self.btn_open_email.clicked.connect(self._open_email_client)
        self.btn_copy_email_addr.clicked.connect(self._copy_email_address)
        self.btn_transfer_email.clicked.connect(self._transfer_email_to_generator)

        self.btn_open_maps.clicked.connect(self._open_maps)
        self.btn_copy_coords.clicked.connect(self._copy_geo_coords)

        self.btn_copy_text.clicked.connect(self._copy_text)

    def keyPressEvent(self, event) -> None:
        """Handle global Ctrl+V in reader tab."""
        if event.matches(Qt.KeySequence.Paste):
            self.decode_from_clipboard()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "QR-Code Bilddatei öffnen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;Alle Dateien (*.*)",
        )
        if file_path:
            self.decode_from_path(Path(file_path))

    def decode_from_path(self, path: Path) -> None:
        """Start decoding from a file path."""
        self.status_label.setText(f"Lese Datei: {path.name}...")
        self._start_worker(path)

    def decode_from_clipboard(self) -> None:
        """Extract image from system clipboard and decode."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        # Check for image data in clipboard
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buffer, "PNG")
                png_bytes = bytes(buffer.data())
                self.status_label.setText("Lese Bild aus Zwischenablage...")
                self._start_worker(png_bytes)
                return

        # Check for image files copied in Windows Explorer
        if mime_data.hasUrls():
            for url in mime_data.urls():
                path = Path(url.toLocalFile())
                if path.is_file() and path.suffix.lower() in (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".bmp",
                    ".webp",
                    ".gif",
                ):
                    self.decode_from_path(path)
                    return

        self.status_label.setText("Kein Bild in der Zwischenablage gefunden.")
        self.status_message.emit("Zwischenablage enthält kein Bild.", 3000)

    def _start_worker(self, source: Path | bytes | Image.Image) -> None:
        if self.active_worker and self.active_worker.isRunning():
            self.active_worker.terminate()
            self.active_worker.wait()

        self.active_worker = DecodeWorker(source)
        self.active_worker.success.connect(self._on_decode_success)
        self.active_worker.failed.connect(self._on_decode_failed)
        self.active_worker.start()

    def _on_decode_success(self, result: ScanResult) -> None:
        self.last_result = result
        self.status_label.setText("✔ QR-Code erfolgreich erkannt!")

        # Log to persistent history
        self.history_manager.add_item(
            action="scan",
            payload_type=result.payload_type.value,
            title=result.title,
            raw_text=result.raw_text,
            metadata=result.metadata,
        )

        if result.payload_type == PayloadType.URL:
            self.result_stack.setCurrentIndex(1)
            self.url_display.setPlainText(result.url or result.raw_text)
            self.status_message.emit("Webadresse erfolgreich dekodiert", 3000)

        elif result.payload_type == PayloadType.WIFI and result.wifi_config:
            self.result_stack.setCurrentIndex(2)
            cfg = result.wifi_config
            hidden_text = " (Versteckt)" if cfg.hidden else ""
            self.wifi_details_label.setText(
                f"<b>Netzwerkname (SSID):</b> {cfg.ssid}{hidden_text}<br>"
                f"<b>Passwort:</b> <code>{cfg.password or '<i>(Kein Passwort)</i>'}</code><br>"
                f"<b>Sicherheit:</b> {cfg.security}"
            )
            self.status_message.emit("WLAN-Zugangsdaten dekodiert", 3000)

        elif result.payload_type == PayloadType.VCARD and result.vcard_config:
            self.result_stack.setCurrentIndex(4)
            vc = result.vcard_config
            name = f"{vc.first_name} {vc.last_name}".strip()
            self.vcard_details_label.setText(
                f"<b>Name:</b> {name or '<i>(Kein Name)</i>'}<br>"
                f"<b>Organisation:</b> {vc.organization or '—'}<br>"
                f"<b>Telefon:</b> {vc.phone or '—'}<br>"
                f"<b>E-Mail:</b> {vc.email or '—'}<br>"
                f"<b>Webseite:</b> {vc.url or '—'}"
            )
            self.status_message.emit("Visitenkarte (vCard) dekodiert", 3000)

        elif result.payload_type == PayloadType.EMAIL and result.email_config:
            self.result_stack.setCurrentIndex(5)
            em = result.email_config
            self.email_details_label.setText(
                f"<b>Empfänger:</b> {em.to or '—'}<br>"
                f"<b>Betreff:</b> {em.subject or '—'}<br>"
                f"<b>Text:</b> <i>{em.body[:120] + ('...' if len(em.body) > 120 else '') or '—'}</i>"
            )
            self.status_message.emit("E-Mail Entwurf dekodiert", 3000)

        elif result.payload_type == PayloadType.GEO and result.geo_config:
            self.result_stack.setCurrentIndex(6)
            gc = result.geo_config
            self.geo_details_label.setText(
                f"<b>Breitengrad (Lat):</b> {gc.latitude:.6f}<br>"
                f"<b>Längengrad (Lon):</b> {gc.longitude:.6f}<br>"
                f"<b>Ort / Beschreibung:</b> {gc.query or '—'}"
            )
            self.status_message.emit("Geo-Koordinaten dekodiert", 3000)

        else:
            self.result_stack.setCurrentIndex(3)
            self.text_display.setPlainText(result.raw_text)
            self.status_message.emit("Text erfolgreich dekodiert", 3000)

    def _on_decode_failed(self, error_msg: str) -> None:
        self.last_result = None
        self.result_stack.setCurrentIndex(0)
        self.status_label.setText(f"❌ {error_msg}")
        self.status_message.emit(error_msg, 3000)

    def _open_url_in_browser(self) -> None:
        if self.last_result and self.last_result.url:
            QDesktopServices.openUrl(QUrl(self.last_result.url))
            self.status_message.emit("Browser geöffnet", 2000)

    def _copy_url(self) -> None:
        if self.last_result and self.last_result.url:
            QApplication.clipboard().setText(self.last_result.url)
            self.status_message.emit("Link in Zwischenablage kopiert!", 2000)

    def _copy_wifi_password(self) -> None:
        if self.last_result and self.last_result.wifi_config:
            QApplication.clipboard().setText(self.last_result.wifi_config.password)
            self.status_message.emit("WLAN-Passwort kopiert!", 2000)

    def _copy_wifi_ssid(self) -> None:
        if self.last_result and self.last_result.wifi_config:
            QApplication.clipboard().setText(self.last_result.wifi_config.ssid)
            self.status_message.emit("WLAN-SSID kopiert!", 2000)

    def _transfer_wifi_to_generator(self) -> None:
        if self.last_result and self.last_result.wifi_config:
            self.request_load_wifi.emit(self.last_result.wifi_config)
            self.status_message.emit("WLAN-Daten in Generator übertragen", 2000)

    def _save_vcf(self) -> None:
        if self.last_result and self.last_result.vcard_config:
            vc = self.last_result.vcard_config
            name = f"{vc.first_name}_{vc.last_name}".strip("_") or "kontakt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Visitenkarte speichern",
                f"{name}.vcf",
                "vCard Datei (*.vcf)",
            )
            if file_path:
                Path(file_path).write_text(self.last_result.raw_text, encoding="utf-8")
                self.status_message.emit(f"Gespeichert: {Path(file_path).name}", 2500)

    def _copy_vcard_phone(self) -> None:
        if self.last_result and self.last_result.vcard_config:
            phone = self.last_result.vcard_config.phone
            if phone:
                QApplication.clipboard().setText(phone)
                self.status_message.emit("Telefonnummer kopiert!", 2000)

    def _copy_vcard_email(self) -> None:
        if self.last_result and self.last_result.vcard_config:
            email = self.last_result.vcard_config.email
            if email:
                QApplication.clipboard().setText(email)
                self.status_message.emit("E-Mail-Adresse kopiert!", 2000)

    def _transfer_vcard_to_generator(self) -> None:
        if self.last_result and self.last_result.vcard_config:
            self.request_load_vcard.emit(self.last_result.vcard_config)
            self.status_message.emit("Kontaktdaten in Generator geladen", 2000)

    def _open_email_client(self) -> None:
        if self.last_result and self.last_result.email_config:
            em = self.last_result.email_config
            mail_uri = format_email_payload(em)
            QDesktopServices.openUrl(QUrl(mail_uri))
            self.status_message.emit("E-Mail-Programm aufgerufen", 2000)

    def _copy_email_address(self) -> None:
        if self.last_result and self.last_result.email_config:
            addr = self.last_result.email_config.to
            if addr:
                QApplication.clipboard().setText(addr)
                self.status_message.emit("E-Mail-Adresse kopiert!", 2000)

    def _transfer_email_to_generator(self) -> None:
        if self.last_result and self.last_result.email_config:
            self.request_load_email.emit(self.last_result.email_config)
            self.status_message.emit("E-Mail-Daten in Generator geladen", 2000)

    def _open_maps(self) -> None:
        if self.last_result and self.last_result.geo_config:
            gc = self.last_result.geo_config
            maps_url = (
                f"https://www.google.com/maps/search/?api=1&query={gc.latitude},{gc.longitude}"
            )
            QDesktopServices.openUrl(QUrl(maps_url))
            self.status_message.emit("Google Maps geöffnet", 2000)

    def _copy_geo_coords(self) -> None:
        if self.last_result and self.last_result.geo_config:
            gc = self.last_result.geo_config
            QApplication.clipboard().setText(f"{gc.latitude:.6f}, {gc.longitude:.6f}")
            self.status_message.emit("Koordinaten kopiert!", 2000)

    def _copy_text(self) -> None:
        if self.last_result:
            QApplication.clipboard().setText(self.last_result.raw_text)
            self.status_message.emit("Text in Zwischenablage kopiert!", 2000)
