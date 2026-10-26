"""Generator tab for creating QR codes with live preview and WiFi templates."""

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from src.core.generator import generate_qr_svg, save_qr_code
from src.core.history import HistoryManager
from src.core.parser import (
    EmailConfig,
    VCardConfig,
    WifiConfig,
    format_email_payload,
    format_vcard_payload,
    format_wifi_payload,
)
from src.gui.dialogs import BatchDialog, CardDialog
from src.gui.workers import GenerateWorker


class GeneratorTab(QWidget):
    """Tab widget for interactive and live QR code generation."""

    status_message = Signal(str, int)

    def __init__(self, history_manager: HistoryManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.history_manager = history_manager

        self.dark_color = "#000000"
        self.light_color = "#ffffff"
        self.finder_color: str | None = None
        self.custom_logo_path: Path | None = None
        self.current_png_bytes: bytes | None = None
        self.active_worker: GenerateWorker | None = None

        # Debounce timer for reactive live preview
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(120)
        self.debounce_timer.timeout.connect(self._start_generation_worker)

        self._setup_ui()
        self._connect_signals()

        # Initial live render
        self._trigger_update()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(24)

        # Left Column: Configuration Controls
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        # Mode Selection
        mode_group = QGroupBox("Inhaltstyp")
        mode_layout = QHBoxLayout(mode_group)
        self.radio_text = QRadioButton("Freitext / URL")
        self.radio_text.setChecked(True)
        self.radio_wifi = QRadioButton("WLAN")
        self.radio_vcard = QRadioButton("Visitenkarte (vCard)")
        self.radio_email = QRadioButton("E-Mail")
        mode_layout.addWidget(self.radio_text)
        mode_layout.addWidget(self.radio_wifi)
        mode_layout.addWidget(self.radio_vcard)
        mode_layout.addWidget(self.radio_email)
        mode_layout.addStretch()
        left_layout.addWidget(mode_group)

        # Content Inputs (Stacked Widget)
        self.input_stack = QStackedWidget()

        # Page 0: Free text / URL
        text_page = QWidget()
        text_layout = QVBoxLayout(text_page)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_label = QLabel("Text oder URL:")
        self.text_input = QPlainTextEdit()
        self.text_input.setPlaceholderText("Gib hier eine Webadresse oder beliebigen Text ein...")
        self.text_input.setPlainText("https://github.com/TGBox/py-qr")
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        self.input_stack.addWidget(text_page)

        # Page 1: WiFi template
        wifi_page = QWidget()
        wifi_layout = QVBoxLayout(wifi_page)
        wifi_layout.setContentsMargins(0, 0, 0, 0)
        wifi_layout.setSpacing(10)

        wifi_layout.addWidget(QLabel("WLAN-Name (SSID):"))
        self.wifi_ssid = QLineEdit()
        self.wifi_ssid.setPlaceholderText("z.B. MeinHeimnetz")
        wifi_layout.addWidget(self.wifi_ssid)

        wifi_layout.addWidget(QLabel("Passwort:"))
        self.wifi_password = QLineEdit()
        self.wifi_password.setPlaceholderText("WLAN-Passwort...")
        wifi_layout.addWidget(self.wifi_password)

        wifi_layout.addWidget(QLabel("Verschlüsselung:"))
        self.wifi_security = QComboBox()
        self.wifi_security.addItems(["WPA / WPA2 / WPA3", "WEP", "Offen (kein Passwort)"])
        wifi_layout.addWidget(self.wifi_security)

        self.wifi_hidden = QCheckBox("Verstecktes Netzwerk (SSID unsichtbar)")
        wifi_layout.addWidget(self.wifi_hidden)
        wifi_layout.addStretch()
        self.input_stack.addWidget(wifi_page)

        # Page 2: vCard template
        vcard_page = QWidget()
        vcard_layout = QVBoxLayout(vcard_page)
        vcard_layout.setContentsMargins(0, 0, 0, 0)
        vcard_layout.setSpacing(6)

        name_row = QHBoxLayout()
        name_left = QVBoxLayout()
        name_left.addWidget(QLabel("Vorname:"))
        self.vcard_first_name = QLineEdit()
        self.vcard_first_name.setPlaceholderText("z.B. Max")
        name_left.addWidget(self.vcard_first_name)
        name_right = QVBoxLayout()
        name_right.addWidget(QLabel("Nachname:"))
        self.vcard_last_name = QLineEdit()
        self.vcard_last_name.setPlaceholderText("z.B. Mustermann")
        name_right.addWidget(self.vcard_last_name)
        name_row.addLayout(name_left)
        name_row.addLayout(name_right)
        vcard_layout.addLayout(name_row)

        vcard_layout.addWidget(QLabel("Firma / Organisation:"))
        self.vcard_org = QLineEdit()
        self.vcard_org.setPlaceholderText("z.B. Musterfirma GmbH")
        vcard_layout.addWidget(self.vcard_org)

        contact_row = QHBoxLayout()
        phone_box = QVBoxLayout()
        phone_box.addWidget(QLabel("Telefon:"))
        self.vcard_phone = QLineEdit()
        self.vcard_phone.setPlaceholderText("+49 170 1234567")
        phone_box.addWidget(self.vcard_phone)
        email_box = QVBoxLayout()
        email_box.addWidget(QLabel("E-Mail:"))
        self.vcard_email = QLineEdit()
        self.vcard_email.setPlaceholderText("max@example.com")
        email_box.addWidget(self.vcard_email)
        contact_row.addLayout(phone_box)
        contact_row.addLayout(email_box)
        vcard_layout.addLayout(contact_row)

        vcard_layout.addWidget(QLabel("Webseite (URL):"))
        self.vcard_url = QLineEdit()
        self.vcard_url.setPlaceholderText("https://example.com")
        vcard_layout.addWidget(self.vcard_url)

        vcard_layout.addWidget(QLabel("Notiz / Funktion:"))
        self.vcard_note = QLineEdit()
        self.vcard_note.setPlaceholderText("z.B. Teamleitung")
        vcard_layout.addWidget(self.vcard_note)

        vcard_layout.addStretch()
        self.input_stack.addWidget(vcard_page)

        # Page 3: Email template
        email_page = QWidget()
        email_layout = QVBoxLayout(email_page)
        email_layout.setContentsMargins(0, 0, 0, 0)
        email_layout.setSpacing(6)

        email_layout.addWidget(QLabel("Empfänger (E-Mail):"))
        self.email_to = QLineEdit()
        self.email_to.setPlaceholderText("kontakt@example.com")
        email_layout.addWidget(self.email_to)

        email_layout.addWidget(QLabel("Betreff:"))
        self.email_subject = QLineEdit()
        self.email_subject.setPlaceholderText("Betreff der E-Mail...")
        email_layout.addWidget(self.email_subject)

        email_layout.addWidget(QLabel("Nachricht:"))
        self.email_body = QPlainTextEdit()
        self.email_body.setPlaceholderText("Vorgefertigter E-Mail-Text...")
        self.email_body.setMaximumHeight(80)
        email_layout.addWidget(self.email_body)

        email_layout.addStretch()
        self.input_stack.addWidget(email_page)

        left_layout.addWidget(self.input_stack)

        # Styling & Error Correction Options
        style_group = QGroupBox("Gestaltung & Korrektur")
        style_layout = QVBoxLayout(style_group)
        style_layout.setSpacing(10)

        colors_layout = QHBoxLayout()
        colors_layout.addWidget(QLabel("Farben:"))

        self.btn_dark_color = QPushButton("Vordergrund")
        self.btn_dark_color.setObjectName("secondaryButton")
        self._update_color_button(self.btn_dark_color, self.dark_color, "Vordergrund")
        colors_layout.addWidget(self.btn_dark_color)

        self.btn_light_color = QPushButton("Hintergrund")
        self.btn_light_color.setObjectName("secondaryButton")
        self._update_color_button(self.btn_light_color, self.light_color, "Hintergrund")
        colors_layout.addWidget(self.btn_light_color)

        self.btn_finder_color = QPushButton("Ecken: Auto")
        self.btn_finder_color.setObjectName("secondaryButton")
        self._update_finder_color_button()
        colors_layout.addWidget(self.btn_finder_color)
        style_layout.addLayout(colors_layout)

        # Module Shape & Logo Options
        artistic_row = QHBoxLayout()
        artistic_row.addWidget(QLabel("Form:"))
        self.combo_shape = QComboBox()
        self.combo_shape.addItem("Quadrat (Klassisch)", "square")
        self.combo_shape.addItem("Punkte (Dots)", "dot")
        self.combo_shape.addItem("Abgerundet (Smooth)", "rounded")
        artistic_row.addWidget(self.combo_shape)

        artistic_row.addWidget(QLabel("Logo / Emblem:"))
        self.combo_logo = QComboBox()
        self.combo_logo.addItem("Kein Logo", None)
        self.combo_logo.addItem("📶 WLAN", "wifi")
        self.combo_logo.addItem("👤 Kontakt", "contact")
        self.combo_logo.addItem("✉️ E-Mail", "email")
        self.combo_logo.addItem("🌐 Webadresse", "url")
        self.combo_logo.addItem("⭐ Stern", "star")
        self.combo_logo.addItem("📁 Eigenes Bild...", "custom")
        artistic_row.addWidget(self.combo_logo)
        style_layout.addLayout(artistic_row)

        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Fehlerkorrektur:"))
        self.combo_error = QComboBox()
        self.combo_error.addItem("M (15% — Standard)", "m")
        self.combo_error.addItem("L (7% — Kompakt)", "l")
        self.combo_error.addItem("Q (25% — Robust)", "q")
        self.combo_error.addItem("H (30% — Maximal / Logo)", "h")
        self.combo_error.setCurrentIndex(0)
        error_layout.addWidget(self.combo_error, stretch=1)

        self.btn_reset_colors = QPushButton("Zurücksetzen")
        self.btn_reset_colors.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.btn_reset_colors.setObjectName("secondaryButton")
        self.btn_reset_colors.setToolTip("Gestaltung und Farben auf Standard zurücksetzen")
        error_layout.addWidget(self.btn_reset_colors)
        style_layout.addLayout(error_layout)

        left_layout.addWidget(style_group)
        main_layout.addWidget(left_column, stretch=3)

        # Right Column: Live Preview & Export
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        preview_group = QGroupBox("Vorschau")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(280, 280)
        self.preview_frame.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;"
        )
        frame_layout = QVBoxLayout(self.preview_frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_frame)

        self.info_label = QLabel("Bereit")
        self.info_label.setObjectName("mutedLabel")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.info_label)
        right_layout.addWidget(preview_group)

        # Action Buttons
        export_group = QGroupBox("Export & Weitergabe")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(8)

        self.btn_copy_clipboard = QPushButton("📋 In Zwischenablage kopieren")
        export_layout.addWidget(self.btn_copy_clipboard)

        export_row = QHBoxLayout()
        self.btn_save_png = QPushButton("💾 Als PNG speichern...")
        self.btn_save_png.setObjectName("secondaryButton")
        self.btn_save_svg = QPushButton("📐 Als SVG speichern...")
        self.btn_save_svg.setObjectName("secondaryButton")
        export_row.addWidget(self.btn_save_png)
        export_row.addWidget(self.btn_save_svg)
        export_layout.addLayout(export_row)

        self.btn_print_card = QPushButton("🖨️ Aufsteller / Kärtchen drucken...")
        self.btn_print_card.setObjectName("secondaryButton")
        export_layout.addWidget(self.btn_print_card)

        self.btn_batch = QPushButton("📦 Stapelverarbeitung...")
        self.btn_batch.setObjectName("secondaryButton")
        export_layout.addWidget(self.btn_batch)

        right_layout.addWidget(export_group)
        right_layout.addStretch()
        main_layout.addWidget(right_column, stretch=2)

    def _connect_signals(self) -> None:
        self.radio_text.toggled.connect(self._on_mode_changed)
        self.radio_wifi.toggled.connect(self._on_mode_changed)
        self.radio_vcard.toggled.connect(self._on_mode_changed)
        self.radio_email.toggled.connect(self._on_mode_changed)

        self.text_input.textChanged.connect(self._trigger_update)
        self.wifi_ssid.textChanged.connect(self._trigger_update)
        self.wifi_password.textChanged.connect(self._trigger_update)
        self.wifi_security.currentIndexChanged.connect(self._trigger_update)
        self.wifi_hidden.toggled.connect(self._trigger_update)

        self.vcard_first_name.textChanged.connect(self._trigger_update)
        self.vcard_last_name.textChanged.connect(self._trigger_update)
        self.vcard_org.textChanged.connect(self._trigger_update)
        self.vcard_phone.textChanged.connect(self._trigger_update)
        self.vcard_email.textChanged.connect(self._trigger_update)
        self.vcard_url.textChanged.connect(self._trigger_update)
        self.vcard_note.textChanged.connect(self._trigger_update)

        self.email_to.textChanged.connect(self._trigger_update)
        self.email_subject.textChanged.connect(self._trigger_update)
        self.email_body.textChanged.connect(self._trigger_update)

        self.combo_error.currentIndexChanged.connect(self._trigger_update)
        self.combo_shape.currentIndexChanged.connect(self._trigger_update)
        self.combo_logo.currentIndexChanged.connect(self._on_logo_changed)

        self.btn_dark_color.clicked.connect(self._pick_dark_color)
        self.btn_light_color.clicked.connect(self._pick_light_color)
        self.btn_finder_color.clicked.connect(self._pick_finder_color)
        self.btn_reset_colors.clicked.connect(self._reset_colors)

        self.btn_copy_clipboard.clicked.connect(self._copy_to_clipboard)
        self.btn_save_png.clicked.connect(self._save_as_png)
        self.btn_save_svg.clicked.connect(self._save_as_svg)
        self.btn_print_card.clicked.connect(self._open_print_studio)
        self.btn_batch.clicked.connect(self.open_batch_studio)

    def _open_print_studio(self) -> None:
        payload, ptype, _ = self.get_current_payload()
        if not payload:
            QMessageBox.warning(self, "Hinweis", "Bitte gib zuerst Daten für den QR-Code ein.")
            return

        shape = self.combo_shape.currentData() or "square"
        logo_data = self.combo_logo.currentData()
        logo_icon = logo_data if logo_data not in (None, "custom") else None
        logo_path = self.custom_logo_path if logo_data == "custom" else None

        dialog = CardDialog(
            qr_data=payload,
            payload_type=ptype,
            dark_color=self.dark_color,
            light_color=self.light_color,
            shape=shape,
            finder_color=self.finder_color,
            logo_icon=logo_icon,
            logo_image_path=logo_path,
            parent=self,
        )
        dialog.exec()

    def open_batch_studio(self) -> None:
        """Open batch processing studio dialog with current styling parameters."""
        shape = self.combo_shape.currentData() or "square"
        logo_data = self.combo_logo.currentData()
        logo_icon = logo_data if logo_data not in (None, "custom") else None
        logo_path = self.custom_logo_path if logo_data == "custom" else None
        error_level = self.combo_error.currentData() or "m"

        dialog = BatchDialog(
            error_level=error_level,
            dark_color=self.dark_color,
            light_color=self.light_color,
            shape=shape,
            finder_color=self.finder_color,
            logo_icon=logo_icon,
            logo_image_path=logo_path,
            parent=self,
        )
        payload, _, _ = self.get_current_payload()
        if payload and not dialog.input_text.toPlainText():
            dialog.input_text.setPlainText(payload)
        dialog.exec()

    def _on_mode_changed(self) -> None:
        if self.radio_wifi.isChecked():
            self.input_stack.setCurrentIndex(1)
            target_err = "h"
        elif self.radio_vcard.isChecked():
            self.input_stack.setCurrentIndex(2)
            target_err = "m"
        elif self.radio_email.isChecked():
            self.input_stack.setCurrentIndex(3)
            target_err = "m"
        else:
            self.input_stack.setCurrentIndex(0)
            target_err = "m"

        for i in range(self.combo_error.count()):
            if self.combo_error.itemData(i) == target_err:
                self.combo_error.setCurrentIndex(i)
                break

        self._trigger_update()

    def _create_color_icon(self, color_hex: str) -> QIcon:
        """Create a 16x16 color swatch icon with a subtle border for contrast."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color_hex))
        painter = QPainter(pixmap)
        border_color = (
            QColor("#94a3b8") if color_hex.lower() in ("#ffffff", "#fff") else QColor("#475569")
        )
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(0, 0, 15, 15)
        painter.end()
        return QIcon(pixmap)

    def _update_color_button(self, btn: QPushButton, color_hex: str, label: str) -> None:
        """Update button label and color swatch icon without breaking light/dark styling."""
        btn.setIcon(self._create_color_icon(color_hex))
        btn.setText(f"{label}: {color_hex.upper()}")
        btn.setStyleSheet("")

    def _update_finder_color_button(self) -> None:
        """Update finder pattern color button label and icon."""
        if self.finder_color:
            self.btn_finder_color.setIcon(self._create_color_icon(self.finder_color))
            self.btn_finder_color.setText(f"Ecken: {self.finder_color.upper()}")
        else:
            self.btn_finder_color.setIcon(self._create_color_icon(self.dark_color))
            self.btn_finder_color.setText("Ecken: Auto")
        self.btn_finder_color.setStyleSheet("")

    def _pick_dark_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.dark_color), self, "Vordergrundfarbe wählen")
        if color.isValid():
            self.dark_color = color.name()
            self._update_color_button(self.btn_dark_color, self.dark_color, "Vordergrund")
            if not self.finder_color:
                self._update_finder_color_button()
            self._trigger_update()

    def _pick_light_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.light_color), self, "Hintergrundfarbe wählen")
        if color.isValid():
            self.light_color = color.name()
            self._update_color_button(self.btn_light_color, self.light_color, "Hintergrund")
            self.preview_frame.setStyleSheet(
                f"background-color: {self.light_color}; border: 1px solid #cbd5e1; border-radius: 8px;"
            )
            self._trigger_update()

    def _pick_finder_color(self) -> None:
        init_col = self.finder_color or self.dark_color
        color = QColorDialog.getColor(QColor(init_col), self, "Ecken-Augen Farbe wählen")
        if color.isValid():
            self.finder_color = color.name()
            self._update_finder_color_button()
            self._trigger_update()

    def _on_logo_changed(self) -> None:
        data = self.combo_logo.currentData()
        if data == "custom":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Logo-Bild für QR-Code auswählen",
                "",
                "Bilddateien (*.png *.jpg *.jpeg *.webp *.bmp *.svg)",
            )
            if file_path:
                self.custom_logo_path = Path(file_path)
                self.combo_logo.setItemText(6, f"📁 {self.custom_logo_path.name[:18]}")
            else:
                if not self.custom_logo_path:
                    self.combo_logo.setCurrentIndex(0)
                    return
        elif data is None:
            self.custom_logo_path = None
            self.combo_logo.setItemText(6, "📁 Eigenes Bild...")

        # Automatically elevate error correction to 'h' for reliable scanability
        if self.combo_logo.currentData() is not None:
            for i in range(self.combo_error.count()):
                if self.combo_error.itemData(i) == "h":
                    self.combo_error.setCurrentIndex(i)
                    break

        self._trigger_update()

    def _reset_colors(self) -> None:
        self.dark_color = "#000000"
        self.light_color = "#ffffff"
        self.finder_color = None
        self.custom_logo_path = None
        self._update_color_button(self.btn_dark_color, self.dark_color, "Vordergrund")
        self._update_color_button(self.btn_light_color, self.light_color, "Hintergrund")
        self._update_finder_color_button()
        self.combo_shape.setCurrentIndex(0)
        self.combo_logo.setCurrentIndex(0)
        self.combo_logo.setItemText(6, "📁 Eigenes Bild...")
        self.preview_frame.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;"
        )
        self._trigger_update()

    def get_current_payload(self) -> tuple[str, str, str]:
        """Return (payload_string, payload_type, title)."""
        if self.radio_wifi.isChecked():
            ssid = self.wifi_ssid.text().strip()
            password = self.wifi_password.text()
            sec_idx = self.wifi_security.currentIndex()
            sec_map = {0: "WPA", 1: "WEP", 2: "nopass"}
            security = sec_map.get(sec_idx, "WPA")
            hidden = self.wifi_hidden.isChecked()

            config = WifiConfig(
                ssid=ssid,
                password=password,
                security=security,
                hidden=hidden,
            )
            payload = format_wifi_payload(config)
            title = f"WLAN: {ssid}" if ssid else "WLAN QR-Code"
            return payload, "wifi", title

        if self.radio_vcard.isChecked():
            config = VCardConfig(
                first_name=self.vcard_first_name.text().strip(),
                last_name=self.vcard_last_name.text().strip(),
                organization=self.vcard_org.text().strip(),
                phone=self.vcard_phone.text().strip(),
                email=self.vcard_email.text().strip(),
                url=self.vcard_url.text().strip(),
                note=self.vcard_note.text().strip(),
            )
            payload = format_vcard_payload(config)
            full_name = f"{config.first_name} {config.last_name}".strip()
            title = f"Kontakt: {full_name}" if full_name else "Visitenkarte (vCard)"
            return payload, "vcard", title

        if self.radio_email.isChecked():
            config = EmailConfig(
                to=self.email_to.text().strip(),
                subject=self.email_subject.text().strip(),
                body=self.email_body.toPlainText().strip(),
            )
            payload = format_email_payload(config)
            title = f"E-Mail: {config.to}" if config.to else "E-Mail QR-Code"
            return payload, "email", title

        text = self.text_input.toPlainText().strip()
        payload_type = "url" if text.startswith(("http://", "https://")) else "text"
        title = text[:35] + ("..." if len(text) > 35 else "")
        return text, payload_type, title or "Text QR-Code"

    def _trigger_update(self) -> None:
        self.debounce_timer.start()

    def _start_generation_worker(self) -> None:
        payload, _, _ = self.get_current_payload()
        if not payload:
            self.preview_label.clear()
            self.info_label.setText("Bitte Text oder Daten eingeben")
            self.current_png_bytes = None
            return

        error_level = self.combo_error.currentData() or "m"

        if self.active_worker and self.active_worker.isRunning():
            self.active_worker.terminate()
            self.active_worker.wait()

        shape = self.combo_shape.currentData() or "square"
        logo_data = self.combo_logo.currentData()
        logo_icon = logo_data if logo_data not in (None, "custom") else None
        logo_path = self.custom_logo_path if logo_data == "custom" else None

        self.active_worker = GenerateWorker(
            data=payload,
            error_level=error_level,
            dark_color=self.dark_color,
            light_color=self.light_color,
            scale=8,
            border=3,
            shape=shape,
            finder_color=self.finder_color,
            logo_icon=logo_icon,
            logo_image_path=logo_path,
        )
        self.active_worker.success.connect(self._on_generation_success)
        self.active_worker.failed.connect(self._on_generation_failed)
        self.active_worker.start()

    def _on_generation_success(self, png_bytes: bytes) -> None:
        self.current_png_bytes = png_bytes
        image = QImage()
        image.loadFromData(QByteArray(png_bytes), "PNG")
        pixmap = QPixmap.fromImage(image)

        scaled = pixmap.scaled(
            260,
            260,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        error_level = self.combo_error.currentData() or "m"
        self.info_label.setText(
            f"Größe: {pixmap.width()}x{pixmap.height()} px | Level: {error_level.upper()}"
        )

    def _on_generation_failed(self, error_msg: str) -> None:
        self.info_label.setText(error_msg)
        self.current_png_bytes = None

    def _copy_to_clipboard(self) -> None:
        if not self.current_png_bytes:
            QMessageBox.warning(self, "Hinweis", "Kein QR-Code zum Kopieren vorhanden.")
            return

        image = QImage()
        image.loadFromData(QByteArray(self.current_png_bytes), "PNG")
        pixmap = QPixmap.fromImage(image)
        QApplication.clipboard().setPixmap(pixmap)

        payload, ptype, title = self.get_current_payload()
        self.history_manager.add_item("generate", ptype, title, payload)
        self.status_message.emit("QR-Code Bild in Zwischenablage kopiert!", 3000)

    def _save_as_png(self) -> None:
        payload, ptype, title = self.get_current_payload()
        if not payload:
            QMessageBox.warning(self, "Hinweis", "Keine Daten zum Speichern vorhanden.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "QR-Code als PNG speichern",
            f"qr_{ptype}.png",
            "PNG Bild (*.png)",
        )
        if file_path:
            error_level = self.combo_error.currentData() or "m"
            shape = self.combo_shape.currentData() or "square"
            logo_data = self.combo_logo.currentData()
            logo_icon = logo_data if logo_data not in (None, "custom") else None
            logo_path = self.custom_logo_path if logo_data == "custom" else None

            save_qr_code(
                data=payload,
                target_path=Path(file_path),
                error_level=error_level,
                dark_color=self.dark_color,
                light_color=self.light_color,
                scale=12,
                shape=shape,
                finder_color=self.finder_color,
                logo_icon=logo_icon,
                logo_image_path=logo_path,
            )
            self.history_manager.add_item("generate", ptype, title, payload)
            self.status_message.emit(f"Gespeichert: {Path(file_path).name}", 3000)

    def _save_as_svg(self) -> None:
        payload, ptype, title = self.get_current_payload()
        if not payload:
            QMessageBox.warning(self, "Hinweis", "Keine Daten zum Speichern vorhanden.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "QR-Code als SVG speichern",
            f"qr_{ptype}.svg",
            "Vektorgrafik (*.svg)",
        )
        if file_path:
            error_level = self.combo_error.currentData() or "m"
            shape = self.combo_shape.currentData() or "square"
            logo_data = self.combo_logo.currentData()
            logo_icon = logo_data if logo_data not in (None, "custom") else None
            logo_path = self.custom_logo_path if logo_data == "custom" else None

            svg_content = generate_qr_svg(
                data=payload,
                error_level=error_level,
                dark_color=self.dark_color,
                light_color=self.light_color,
                shape=shape,
                finder_color=self.finder_color,
                logo_icon=logo_icon,
                logo_image_path=logo_path,
            )
            Path(file_path).write_text(svg_content, encoding="utf-8")
            self.history_manager.add_item("generate", ptype, title, payload)
            self.status_message.emit(f"Gespeichert: {Path(file_path).name}", 3000)

    def load_wifi_data(self, config: WifiConfig) -> None:
        """Pre-populate the WiFi form with existing WiFi config."""
        self.radio_wifi.setChecked(True)
        self.wifi_ssid.setText(config.ssid)
        self.wifi_password.setText(config.password)
        sec_str = config.security.upper()
        if sec_str in ("WPA", "WPA2", "WPA3"):
            self.wifi_security.setCurrentIndex(0)
        elif sec_str == "WEP":
            self.wifi_security.setCurrentIndex(1)
        else:
            self.wifi_security.setCurrentIndex(2)
        self.wifi_hidden.setChecked(config.hidden)
        self._trigger_update()

    def load_vcard_data(self, config: VCardConfig) -> None:
        """Pre-populate the vCard form with existing VCardConfig."""
        self.radio_vcard.setChecked(True)
        self.vcard_first_name.setText(config.first_name)
        self.vcard_last_name.setText(config.last_name)
        self.vcard_org.setText(config.organization)
        self.vcard_phone.setText(config.phone)
        self.vcard_email.setText(config.email)
        self.vcard_url.setText(config.url)
        self.vcard_note.setText(config.note)
        self._trigger_update()

    def load_email_data(self, config: EmailConfig) -> None:
        """Pre-populate the Email form with existing EmailConfig."""
        self.radio_email.setChecked(True)
        self.email_to.setText(config.to)
        self.email_subject.setText(config.subject)
        self.email_body.setPlainText(config.body)
        self._trigger_update()
