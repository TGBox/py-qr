"""Generator tab for creating QR codes with live preview and WiFi templates."""

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
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
    QVBoxLayout,
    QWidget,
)

from src.core.generator import generate_qr_svg, save_qr_code
from src.core.history import HistoryManager
from src.core.parser import WifiConfig, format_wifi_payload
from src.gui.workers import GenerateWorker


class GeneratorTab(QWidget):
    """Tab widget for interactive and live QR code generation."""

    status_message = Signal(str, int)

    def __init__(self, history_manager: HistoryManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.history_manager = history_manager

        self.dark_color = "#000000"
        self.light_color = "#ffffff"
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
        self.radio_wifi = QRadioButton("WLAN-Netzwerk")
        mode_layout.addWidget(self.radio_text)
        mode_layout.addWidget(self.radio_wifi)
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

        self.btn_reset_colors = QPushButton("↺")
        self.btn_reset_colors.setObjectName("secondaryButton")
        self.btn_reset_colors.setToolTip("Farben auf Standard zurücksetzen")
        self.btn_reset_colors.setMaximumWidth(36)
        colors_layout.addWidget(self.btn_reset_colors)
        style_layout.addLayout(colors_layout)

        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Fehlerkorrektur:"))
        self.combo_error = QComboBox()
        self.combo_error.addItem("M (15% — Standard)", "m")
        self.combo_error.addItem("L (7% — Kompakt)", "l")
        self.combo_error.addItem("Q (25% — Robust)", "q")
        self.combo_error.addItem("H (30% — Maximal / Druck)", "h")
        self.combo_error.setCurrentIndex(0)
        error_layout.addWidget(self.combo_error)
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

        right_layout.addWidget(export_group)
        right_layout.addStretch()
        main_layout.addWidget(right_column, stretch=2)

    def _connect_signals(self) -> None:
        self.radio_text.toggled.connect(self._on_mode_changed)
        self.radio_wifi.toggled.connect(self._on_mode_changed)

        self.text_input.textChanged.connect(self._trigger_update)
        self.wifi_ssid.textChanged.connect(self._trigger_update)
        self.wifi_password.textChanged.connect(self._trigger_update)
        self.wifi_security.currentIndexChanged.connect(self._trigger_update)
        self.wifi_hidden.toggled.connect(self._trigger_update)
        self.combo_error.currentIndexChanged.connect(self._trigger_update)

        self.btn_dark_color.clicked.connect(self._pick_dark_color)
        self.btn_light_color.clicked.connect(self._pick_light_color)
        self.btn_reset_colors.clicked.connect(self._reset_colors)

        self.btn_copy_clipboard.clicked.connect(self._copy_to_clipboard)
        self.btn_save_png.clicked.connect(self._save_as_png)
        self.btn_save_svg.clicked.connect(self._save_as_svg)

    def _on_mode_changed(self) -> None:
        if self.radio_wifi.isChecked():
            self.input_stack.setCurrentIndex(1)
            # Switch to High error correction for WiFi/printing by default
            for i in range(self.combo_error.count()):
                if self.combo_error.itemData(i) == "h":
                    self.combo_error.setCurrentIndex(i)
                    break
        else:
            self.input_stack.setCurrentIndex(0)
            # Switch back to Medium error correction for text
            for i in range(self.combo_error.count()):
                if self.combo_error.itemData(i) == "m":
                    self.combo_error.setCurrentIndex(i)
                    break
        self._trigger_update()

    def _update_color_button(self, btn: QPushButton, color_hex: str, label: str) -> None:
        text_color = (
            "#ffffff" if color_hex.lower() in ("#000000", "#1e293b", "#0f172a") else "#000000"
        )
        btn.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; font-weight: bold;")
        btn.setText(f"{label}: {color_hex.upper()}")

    def _pick_dark_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.dark_color), self, "Vordergrundfarbe wählen")
        if color.isValid():
            self.dark_color = color.name()
            self._update_color_button(self.btn_dark_color, self.dark_color, "Vordergrund")
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

    def _reset_colors(self) -> None:
        self.dark_color = "#000000"
        self.light_color = "#ffffff"
        self._update_color_button(self.btn_dark_color, self.dark_color, "Vordergrund")
        self._update_color_button(self.btn_light_color, self.light_color, "Hintergrund")
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

        self.active_worker = GenerateWorker(
            data=payload,
            error_level=error_level,
            dark_color=self.dark_color,
            light_color=self.light_color,
            scale=8,
            border=3,
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
            save_qr_code(
                data=payload,
                target_path=Path(file_path),
                error_level=error_level,
                dark_color=self.dark_color,
                light_color=self.light_color,
                scale=12,
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
            svg_content = generate_qr_svg(
                data=payload,
                error_level=error_level,
                dark_color=self.dark_color,
                light_color=self.light_color,
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
