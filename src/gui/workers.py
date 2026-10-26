"""Background worker threads for decoding and generating QR codes."""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QThread, Signal

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
