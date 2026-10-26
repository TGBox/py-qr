"""Background worker threads for decoding and generating QR codes."""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QThread, Signal

from src.core.batch_processor import generate_batch_pdf_sheet, generate_batch_zip
from src.core.generator import generate_qr_png_bytes
from src.core.reader import decode_image


class DecodeWorker(QThread):
    """Worker thread for decoding QR images asynchronously."""

    success = Signal(object)  # ScanResult
    failed = Signal(str)

    def __init__(self, source: Path | str | bytes | Image.Image):
        super().__init__()
        self.source = source

    def run(self) -> None:
        try:
            result = decode_image(self.source)
            if result:
                self.success.emit(result)
            else:
                self.failed.emit("Kein QR-Code im Bild gefunden.")
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"Fehler beim Dekodieren: {e}")


class GenerateWorker(QThread):
    """Worker thread for generating QR PNG bytes asynchronously."""

    success = Signal(bytes)
    failed = Signal(str)

    def __init__(
        self,
        data: str,
        error_level: str = "m",
        dark_color: str = "#000000",
        light_color: str = "#ffffff",
        scale: int = 10,
        border: int = 4,
        shape: str = "square",
        finder_color: str | None = None,
        logo_icon: str | None = None,
        logo_image_path: Path | str | None = None,
    ):
        super().__init__()
        self.data = data
        self.error_level = error_level
        self.dark_color = dark_color
        self.light_color = light_color
        self.scale = scale
        self.border = border
        self.shape = shape
        self.finder_color = finder_color
        self.logo_icon = logo_icon
        self.logo_image_path = logo_image_path

    def run(self) -> None:
        try:
            if not self.data.strip():
                self.failed.emit("Keine Daten zum Generieren vorhanden.")
                return

            png_bytes = generate_qr_png_bytes(
                data=self.data,
                error_level=self.error_level,
                dark_color=self.dark_color,
                light_color=self.light_color,
                scale=self.scale,
                border=self.border,
                shape=self.shape,  # type: ignore[arg-type]
                finder_color=self.finder_color,
                logo_icon=self.logo_icon,
                logo_image_path=self.logo_image_path,
            )
            self.success.emit(png_bytes)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"Fehler beim Erstellen des QR-Codes: {e}")


class BatchWorker(QThread):
    """Worker thread for generating batch QR codes into ZIP or PDF."""

    progress = Signal(int, int)  # current, total
    success = Signal(str, int)  # message, generated_count
    failed = Signal(str)

    def __init__(
        self,
        items: list,
        target_path: Path,
        mode: str = "zip",  # "zip" or "pdf"
        format_type: str = "png",  # for zip: "png" or "svg"
        layout: str = "24_labels",  # for pdf: "24_labels" or "8_cards"
        error_level: str = "m",
        dark_color: str = "#000000",
        light_color: str = "#ffffff",
        shape: str = "square",
        finder_color: str | None = None,
        logo_icon: str | None = None,
        logo_image_path: Path | str | None = None,
    ):
        super().__init__()
        self.items = items
        self.target_path = Path(target_path)
        self.mode = mode
        self.format_type = format_type
        self.layout = layout
        self.error_level = error_level
        self.dark_color = dark_color
        self.light_color = light_color
        self.shape = shape
        self.finder_color = finder_color
        self.logo_icon = logo_icon
        self.logo_image_path = logo_image_path
        self.is_cancelled = False

    def cancel(self) -> None:
        """Cooperatively request cancellation."""
        self.is_cancelled = True

    def _progress_cb(self, current: int, total: int) -> bool:
        if self.is_cancelled:
            return False
        self.progress.emit(current, total)
        return True

    def run(self) -> None:
        try:
            if not self.items:
                self.failed.emit("Keine Datensätze zum Verarbeiten vorhanden.")
                return

            if self.mode == "zip":
                count = generate_batch_zip(
                    items=self.items,
                    target_zip_path=self.target_path,
                    format_type=self.format_type,  # type: ignore[arg-type]
                    error_level=self.error_level,
                    dark_color=self.dark_color,
                    light_color=self.light_color,
                    shape=self.shape,
                    finder_color=self.finder_color,
                    logo_icon=self.logo_icon,
                    logo_image_path=self.logo_image_path,
                    progress_callback=self._progress_cb,
                )
                if self.is_cancelled:
                    self.failed.emit("Stapelverarbeitung wurde abgebrochen.")
                else:
                    self.success.emit(f"{count} QR-Codes erfolgreich als ZIP gespeichert.", count)
            elif self.mode == "pdf":
                count = generate_batch_pdf_sheet(
                    items=self.items,
                    target_pdf_path=self.target_path,
                    layout=self.layout,  # type: ignore[arg-type]
                    dark_color=self.dark_color,
                    light_color=self.light_color,
                    shape=self.shape,
                    finder_color=self.finder_color,
                    logo_icon=self.logo_icon,
                    logo_image_path=self.logo_image_path,
                    progress_callback=self._progress_cb,
                )
                if self.is_cancelled:
                    self.failed.emit("Stapelverarbeitung wurde abgebrochen.")
                else:
                    self.success.emit(
                        f"Druckbogen mit {count} QR-Codes als PDF gespeichert.", count
                    )
            else:
                self.failed.emit(f"Unbekannter Modus: {self.mode}")
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"Fehler bei der Stapelverarbeitung: {e}")
