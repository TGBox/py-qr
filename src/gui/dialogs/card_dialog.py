"""Dialog for designing and exporting printable QR code cards and table stands."""

from pathlib import Path
from typing import Literal

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.card_printer import (
    CardConfig,
    render_card_to_image,
    render_card_to_pdf,
    render_card_to_png,
)
from src.core.parser import parse_payload


class CardDialog(QDialog):
    """Dialog allowing users to customize and export a printable stand/card."""

    def __init__(
        self,
        qr_data: str,
        payload_type: str,
        dark_color: str = "#000000",
        light_color: str = "#ffffff",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.qr_data = qr_data
        self.payload_type = payload_type
        self.dark_color = dark_color
        self.light_color = light_color

        self.setWindowTitle("🖨️ Aufsteller & Kärtchen-Studio")
        self.resize(760, 560)
        self.setMinimumSize(680, 500)

        self._init_defaults()
        self._setup_ui()
        self._connect_signals()

        # Initial preview render
        QTimer.singleShot(50, self._update_preview)

    def _init_defaults(self) -> None:
        """Infer suitable defaults depending on payload type."""
        parsed = parse_payload(self.qr_data)

        if self.payload_type == "wifi" and parsed.wifi_config:
            self.default_title = "Gäste-WLAN"
            self.default_subtitle = "Scanne den QR-Code, um dich direkt zu verbinden"
            self.info_items: list[tuple[str, str]] = [
                ("WLAN-Name (SSID)", parsed.wifi_config.ssid or "WLAN"),
                ("Passwort", parsed.wifi_config.password or "(Ohne Passwort)"),
                ("Verschlüsselung", parsed.wifi_config.security),
            ]
        elif self.payload_type == "vcard" and parsed.vcard_config:
            vc = parsed.vcard_config
            name = f"{vc.first_name} {vc.last_name}".strip()
            self.default_title = name or "Visitenkarte"
            self.default_subtitle = vc.organization or "Kontaktdaten"
            self.info_items = []
            if vc.phone:
                self.info_items.append(("Telefon", vc.phone))
            if vc.email:
                self.info_items.append(("E-Mail", vc.email))
            if vc.url:
                self.info_items.append(("Webseite", vc.url))
        else:
            self.default_title = "QR-Code Information"
            self.default_subtitle = "Scanne den Code mit deinem Smartphone"
            preview_val = self.qr_data[:35] + ("..." if len(self.qr_data) > 35 else "")
            self.info_items = [("Inhalt", preview_val)]

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(20)

        # Left Column: Configuration Controls
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        config_group = QGroupBox("Aufsteller-Gestaltung")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        config_layout.addWidget(QLabel("Überschrift / Titel:"))
        self.input_title = QLineEdit(self.default_title)
        config_layout.addWidget(self.input_title)

        config_layout.addWidget(QLabel("Untertitel / Hinweis:"))
        self.input_subtitle = QLineEdit(self.default_subtitle)
        config_layout.addWidget(self.input_subtitle)

        config_layout.addWidget(QLabel("Druckformat:"))
        self.combo_size = QComboBox()
        self.combo_size.addItem("DIN A6 (Tischaufsteller / 105 × 148 mm)", "A6")
        self.combo_size.addItem("DIN A4 (Aushang / 210 × 297 mm)", "A4")
        config_layout.addWidget(self.combo_size)

        config_layout.addWidget(QLabel("Fußzeile:"))
        self.input_footer = QLineEdit("Schnell & sicher verbunden")
        config_layout.addWidget(self.input_footer)

        left_layout.addWidget(config_group)

        # Action Buttons
        export_group = QGroupBox("Druck & Export")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(10)

        self.btn_export_pdf = QPushButton("📄 Druckfertiges PDF speichern...")
        export_layout.addWidget(self.btn_export_pdf)

        self.btn_export_png = QPushButton("🖼️ Hochauflösendes PNG speichern...")
        self.btn_export_png.setObjectName("secondaryButton")
        export_layout.addWidget(self.btn_export_png)

        left_layout.addWidget(export_group)

        left_layout.addStretch()
        self.btn_close = QPushButton("Schließen")
        self.btn_close.setObjectName("secondaryButton")
        left_layout.addWidget(self.btn_close)

        main_layout.addWidget(left_box, stretch=3)

        # Right Column: Live Card Preview
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        preview_group = QGroupBox("Druckvorschau")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;"
        )
        frame_layout = QVBoxLayout(self.preview_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_frame)

        self.preview_info = QLabel("DIN A6 • 300 DPI Druckauflösung")
        self.preview_info.setObjectName("mutedLabel")
        self.preview_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_info)

        right_layout.addWidget(preview_group)
        main_layout.addWidget(right_box, stretch=3)

    def _connect_signals(self) -> None:
        self.input_title.textChanged.connect(self._update_preview)
        self.input_subtitle.textChanged.connect(self._update_preview)
        self.combo_size.currentIndexChanged.connect(self._update_preview)
        self.input_footer.textChanged.connect(self._update_preview)

        self.btn_export_pdf.clicked.connect(self._export_pdf)
        self.btn_export_png.clicked.connect(self._export_png)
        self.btn_close.clicked.connect(self.accept)

    def _get_card_config(self) -> CardConfig:
        page_size: Literal["A6", "A4"] = self.combo_size.currentData() or "A6"
        return CardConfig(
            title=self.input_title.text().strip(),
            subtitle=self.input_subtitle.text().strip(),
            qr_data=self.qr_data,
            info_items=self.info_items,
            footer=self.input_footer.text().strip(),
            page_size=page_size,
            dark_color=self.dark_color,
            light_color=self.light_color,
        )

    def _update_preview(self) -> None:
        config = self._get_card_config()
        # Fast preview render at 100 DPI
        img = render_card_to_image(config, dpi=100)
        pixmap = QPixmap.fromImage(img)
        scaled = pixmap.scaled(
            270,
            380,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        self.preview_info.setText(f"{config.page_size} • 300 DPI Druckqualität")

    def _export_pdf(self) -> None:
        config = self._get_card_config()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Aufsteller als PDF drucken / speichern",
            f"aufsteller_{config.page_size.lower()}.pdf",
            "PDF-Dokument (*.pdf)",
        )
        if file_path:
            render_card_to_pdf(config, Path(file_path))
            QMessageBox.information(
                self,
                "PDF erfolgreich erstellt",
                f"Der Aufsteller wurde erfolgreich gespeichert:\n{Path(file_path).name}",
            )

    def _export_png(self) -> None:
        config = self._get_card_config()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Aufsteller als hochauflösendes PNG speichern",
            f"aufsteller_{config.page_size.lower()}.png",
            "PNG-Grafik (*.png)",
        )
        if file_path:
            render_card_to_png(config, Path(file_path), dpi=300)
            QMessageBox.information(
                self,
                "PNG erfolgreich erstellt",
                f"Die Grafik wurde in 300 DPI gespeichert:\n{Path(file_path).name}",
            )
