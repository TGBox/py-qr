"""Dialog for batch processing and dual export (ZIP archive or DIN A4 PDF sheet)."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.batch_processor import BatchItem, parse_batch_file, parse_batch_text
from src.gui.workers import BatchWorker


class BatchDialog(QDialog):
    """Dialog allowing users to batch generate QR codes from lists/CSVs to ZIP or PDF."""

    def __init__(
        self,
        error_level: str = "m",
        dark_color: str = "#000000",
        light_color: str = "#ffffff",
        shape: str = "square",
        finder_color: str | None = None,
        logo_icon: str | None = None,
        logo_image_path: Path | str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.error_level = error_level
        self.dark_color = dark_color
        self.light_color = light_color
        self.shape = shape
        self.finder_color = finder_color
        self.logo_icon = logo_icon
        self.logo_image_path = logo_image_path

        self.items: list[BatchItem] = []
        self.worker: BatchWorker | None = None

        self.setWindowTitle("📦 Stapelverarbeitung (Batch-Studio)")
        self.resize(920, 620)
        self.setMinimumSize(780, 520)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._parse_and_refresh_table)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Header description
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title_lbl = QLabel("📦 QR-Code Stapelverarbeitung")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        desc_lbl = QLabel(
            "Verarbeite tabellarische Daten, CSV-Dateien oder Listen aus der Zwischenablage "
            "zu einem ZIP-Archiv oder druckfertigen DIN A4 Bogen."
        )
        desc_lbl.setObjectName("mutedLabel")
        desc_lbl.setWordWrap(True)
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(desc_lbl)
        main_layout.addLayout(header_layout)

        # Splitter: Left Controls vs. Right Preview Table
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Column: Input and Export Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 1. Input Group
        input_group = QGroupBox("1. Eingabedaten")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(8)

        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText(
            "Trage hier deine Daten ein (eine Zeile pro QR-Code).\n\n"
            "Beispiele:\n"
            "https://example.com/produkt1;Produkt 1\n"
            "https://example.com/produkt2;Produkt 2\n\n"
            "Oder füge direkt Spalten aus Excel ein (Komma, Semikolon oder Tab)."
        )
        input_layout.addWidget(self.input_text)

        # Input buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_paste = QPushButton("📋 Einfügen")
        self.btn_paste.setObjectName("secondaryButton")
        self.btn_import = QPushButton("📁 CSV / TXT öffnen...")
        self.btn_import.setObjectName("secondaryButton")
        self.btn_clear = QPushButton("🗑️ Leeren")
        self.btn_clear.setObjectName("secondaryButton")

        btn_row.addWidget(self.btn_paste)
        btn_row.addWidget(self.btn_import)
        btn_row.addWidget(self.btn_clear)
        input_layout.addLayout(btn_row)

        self.lbl_count = QLabel("0 Einträge erkannt")
        self.lbl_count.setStyleSheet("font-weight: 600; color: #3b82f6;")
        input_layout.addWidget(self.lbl_count)

        left_layout.addWidget(input_group)

        # 2. Export Mode Group
        export_group = QGroupBox("2. Ausgabe-Format")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(10)

        self.radio_zip = QRadioButton("📦 ZIP-Archiv (Einzelne Bilddateien)")
        self.radio_zip.setChecked(True)
        export_layout.addWidget(self.radio_zip)

        self.zip_options_layout = QHBoxLayout()
        self.zip_options_layout.setContentsMargins(24, 0, 0, 0)
        self.zip_options_layout.addWidget(QLabel("Dateiformat:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG-Grafik (.png)", "SVG-Vektorgrafik (.svg)"])
        self.zip_options_layout.addWidget(self.combo_format)
        self.zip_options_layout.addStretch()
        export_layout.addLayout(self.zip_options_layout)

        self.radio_pdf = QRadioButton("📄 PDF-Druckbogen (DIN A4 Etiketten & Kärtchen)")
        export_layout.addWidget(self.radio_pdf)

        self.pdf_options_layout = QHBoxLayout()
        self.pdf_options_layout.setContentsMargins(24, 0, 0, 0)
        self.pdf_options_layout.addWidget(QLabel("Bogen-Aufteilung:"))
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(
            ["24 Etiketten (3 × 8 Raster)", "8 Aufsteller/Kärtchen (2 × 4 Raster)"]
        )
        self.pdf_options_layout.addWidget(self.combo_layout)
        self.pdf_options_layout.addStretch()
        export_layout.addLayout(self.pdf_options_layout)

        # Mode button group
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_zip)
        self.mode_group.addButton(self.radio_pdf)

        left_layout.addWidget(export_group)

        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("mutedLabel")
        self.lbl_status.setVisible(False)
        left_layout.addWidget(self.lbl_status)

        left_layout.addStretch()

        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        self.btn_start = QPushButton("🚀 Stapelverarbeitung starten...")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setEnabled(False)

        self.btn_close = QPushButton("Schließen")
        self.btn_close.setObjectName("secondaryButton")

        action_layout.addWidget(self.btn_start, 2)
        action_layout.addWidget(self.btn_close, 1)
        left_layout.addLayout(action_layout)

        splitter.addWidget(left_widget)

        # Right Column: Live Preview Table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        table_group = QGroupBox("Erkannte QR-Code Einträge (Live-Vorschau)")
        table_layout = QVBoxLayout(table_group)

        self.table_preview = QTableWidget(0, 3)
        self.table_preview.setHorizontalHeaderLabels(["#", "Inhalt / URL", "Beschriftung (Label)"])
        self.table_preview.setAlternatingRowColors(True)
        self.table_preview.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        header = self.table_preview.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.table_preview)
        right_layout.addWidget(table_group)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 5)

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.input_text.textChanged.connect(self._debounce_timer.start)
        self.btn_paste.clicked.connect(self._paste_from_clipboard)
        self.btn_import.clicked.connect(self._import_from_file)
        self.btn_clear.clicked.connect(self._clear_input)
        self.btn_start.clicked.connect(self._start_batch)
        self.btn_close.clicked.connect(self.close)

        self.radio_zip.toggled.connect(self._update_format_visibility)
        self.radio_pdf.toggled.connect(self._update_format_visibility)
        self._update_format_visibility()

    def _update_format_visibility(self) -> None:
        zip_active = self.radio_zip.isChecked()
        self.combo_format.setEnabled(zip_active)
        self.combo_layout.setEnabled(not zip_active)

    def _paste_from_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text.strip():
            self.input_text.setPlainText(text.strip())

    def _import_from_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV- oder Textdatei importieren",
            "",
            "Textdateien (*.csv *.txt *.tsv);;Alle Dateien (*.*)",
        )
        if not file_path:
            return

        try:
            items = parse_batch_file(Path(file_path))
            lines: list[str] = []
            for it in items:
                if it.label:
                    lines.append(f"{it.payload};{it.label}")
                else:
                    lines.append(it.payload)
            self.input_text.setPlainText("\n".join(lines))
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Import-Fehler", f"Datei konnte nicht gelesen werden:\n{e}")

    def _clear_input(self) -> None:
        self.input_text.clear()
        self.table_preview.setRowCount(0)
        self.items = []
        self.lbl_count.setText("0 Einträge erkannt")
        self.btn_start.setEnabled(False)

    def _parse_and_refresh_table(self) -> None:
        raw_text = self.input_text.toPlainText().strip()
        if not raw_text:
            self._clear_input()
            return

        self.items = parse_batch_text(raw_text)
        count = len(self.items)
        self.lbl_count.setText(f"{count} {'Eintrag' if count == 1 else 'Einträge'} erkannt")
        self.btn_start.setEnabled(count > 0)

        # Update preview table (cap at 300 rows for preview speed)
        preview_items = self.items[:300]
        self.table_preview.setRowCount(len(preview_items))
        for row_idx, item in enumerate(preview_items, start=1):
            idx_item = QTableWidgetItem(f"{row_idx}")
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            payload_item = QTableWidgetItem(item.payload)
            label_item = QTableWidgetItem(item.get_effective_label(row_idx))

            self.table_preview.setItem(row_idx - 1, 0, idx_item)
            self.table_preview.setItem(row_idx - 1, 1, payload_item)
            self.table_preview.setItem(row_idx - 1, 2, label_item)

    def _start_batch(self) -> None:
        if not self.items:
            QMessageBox.information(
                self, "Hinweis", "Bitte gib zuerst mindestens einen Eintrag ein."
            )
            return

        if self.radio_zip.isChecked():
            mode = "zip"
            ext = "svg" if self.combo_format.currentIndex() == 1 else "png"
            target, _ = QFileDialog.getSaveFileName(
                self,
                "ZIP-Archiv speichern",
                "qr_codes_stapel.zip",
                "ZIP-Archiv (*.zip)",
            )
            layout = "24_labels"
        else:
            mode = "pdf"
            ext = "png"
            layout = "8_cards" if self.combo_layout.currentIndex() == 1 else "24_labels"
            target, _ = QFileDialog.getSaveFileName(
                self,
                "PDF-Druckbogen speichern",
                "qr_druckbogen.pdf",
                "PDF-Dokument (*.pdf)",
            )

        if not target:
            return

        # Disable interactive UI during processing
        self._set_ui_busy(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText(f"Starte Stapelverarbeitung für {len(self.items)} Codes...")
        self.lbl_status.setVisible(True)

        self.worker = BatchWorker(
            items=self.items,
            target_path=Path(target),
            mode=mode,
            format_type=ext,
            layout=layout,
            error_level=self.error_level,
            dark_color=self.dark_color,
            light_color=self.light_color,
            shape=self.shape,
            finder_color=self.finder_color,
            logo_icon=self.logo_icon,
            logo_image_path=self.logo_image_path,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.lbl_status.setText(f"Erstelle QR-Code {current} von {total} ({pct}%)...")

    def _on_success(self, message: str, count: int) -> None:
        self._set_ui_busy(False)
        self.progress_bar.setValue(100)
        self.lbl_status.setText(message)
        QMessageBox.information(self, "Erfolg", message)

    def _on_failed(self, error_msg: str) -> None:
        self._set_ui_busy(False)
        self.lbl_status.setText(f"Fehler: {error_msg}")
        QMessageBox.warning(self, "Stapelverarbeitung", error_msg)

    def _set_ui_busy(self, busy: bool) -> None:
        self.input_text.setEnabled(not busy)
        self.btn_paste.setEnabled(not busy)
        self.btn_import.setEnabled(not busy)
        self.btn_clear.setEnabled(not busy)
        self.btn_start.setEnabled(not busy)
        self.radio_zip.setEnabled(not busy)
        self.radio_pdf.setEnabled(not busy)
        self.combo_format.setEnabled(not busy and self.radio_zip.isChecked())
        self.combo_layout.setEnabled(not busy and self.radio_pdf.isChecked())
        if busy:
            self.btn_close.setText("Abbrechen")
        else:
            self.btn_close.setText("Schließen")

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
        super().closeEvent(event)
