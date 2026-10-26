"""History tab displaying recent scans and generations with quick actions."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.history import HistoryItem, HistoryManager


class HistoryTab(QWidget):
    """Tab widget for viewing and managing saved QR code activity."""

    status_message = Signal(str, int)

    def __init__(self, history_manager: HistoryManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.items: list[HistoryItem] = []

        self._setup_ui()
        self._connect_signals()
        self.refresh_history()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Top Header Bar
        header_layout = QHBoxLayout()
        self.header_label = QLabel("Zuletzt erstellte und gescannte QR-Codes")
        self.header_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("↺ Aktualisieren")
        self.btn_refresh.setObjectName("secondaryButton")
        header_layout.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("🗑 Verlauf leeren")
        self.btn_clear.setObjectName("dangerButton")
        header_layout.addWidget(self.btn_clear)
        layout.addLayout(header_layout)

        # History List
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=2)

        # Selected Item Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        details_header = QHBoxLayout()
        self.details_title = QLabel("Inhalt des ausgewählten Eintrags:")
        self.details_title.setStyleSheet("font-weight: bold;")
        details_header.addWidget(self.details_title)
        details_header.addStretch()

        self.btn_copy_detail = QPushButton("📋 Inhalt kopieren")
        self.btn_copy_detail.setEnabled(False)
        details_header.addWidget(self.btn_copy_detail)

        self.btn_delete_item = QPushButton("Eintrag entfernen")
        self.btn_delete_item.setObjectName("secondaryButton")
        self.btn_delete_item.setEnabled(False)
        details_header.addWidget(self.btn_delete_item)
        details_layout.addLayout(details_header)

        self.detail_text = QPlainTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(120)
        details_layout.addWidget(self.detail_text)

        layout.addLayout(details_layout, stretch=1)

    def _connect_signals(self) -> None:
        self.btn_refresh.clicked.connect(self.refresh_history)
        self.btn_clear.clicked.connect(self._confirm_clear)
        self.list_widget.currentRowChanged.connect(self._on_item_selected)
        self.btn_copy_detail.clicked.connect(self._copy_selected_text)
        self.btn_delete_item.clicked.connect(self._delete_selected_item)

    def showEvent(self, event: QShowEvent) -> None:
        """Auto-refresh when switching into the history tab."""
        super().showEvent(event)
        self.refresh_history()

    def refresh_history(self) -> None:
        """Reload entries from storage and populate the list widget."""
        self.list_widget.clear()
        self.items = self.history_manager.get_items()

        count = len(self.items)
        max_limit = self.history_manager.max_items
        self.header_label.setText(
            f"Zuletzt erstellte und gescannte QR-Codes ({count} von max. {max_limit})"
        )

        if not self.items:
            empty_item = QListWidgetItem("Keine Einträge im Verlauf vorhanden.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(empty_item)
            self._clear_details()
            return

        for item in self.items:
            action_symbol = "📥 Gelesen" if item.action == "scan" else "⚡ Erstellt"
            type_symbol = item.payload_type.upper()
            display_text = f"[{action_symbol} | {type_symbol}]  {item.title}  —  {item.timestamp}"

            list_item = QListWidgetItem(display_text)
            self.list_widget.addItem(list_item)

        # Select first item by default
        self.list_widget.setCurrentRow(0)

    def _on_item_selected(self, row: int) -> None:
        if 0 <= row < len(self.items):
            item = self.items[row]
            self.detail_text.setPlainText(item.raw_text)
            self.btn_copy_detail.setEnabled(True)
            self.btn_delete_item.setEnabled(True)
        else:
            self._clear_details()

    def _clear_details(self) -> None:
        self.detail_text.clear()
        self.btn_copy_detail.setEnabled(False)
        self.btn_delete_item.setEnabled(False)

    def _copy_selected_text(self) -> None:
        text = self.detail_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_message.emit("Inhalt in die Zwischenablage kopiert!", 2000)

    def _delete_selected_item(self) -> None:
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.items):
            item = self.items[row]
            self.history_manager.delete_item(item.id)
            self.refresh_history()
            self.status_message.emit("Eintrag gelöscht", 2000)

    def _confirm_clear(self) -> None:
        reply = QMessageBox.question(
            self,
            "Verlauf leeren?",
            "Möchtest du den gesamten Verlauf wirklich unwiderruflich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.refresh_history()
            self.status_message.emit("Verlauf wurde geleert.", 3000)
