"""QR code decoding module using zxing-cpp and Pillow."""

import io
from pathlib import Path

import zxingcpp
from PIL import Image, UnidentifiedImageError

from src.core.parser import ScanResult, parse_payload


def decode_image(source: Path | str | bytes | Image.Image) -> ScanResult | None:
    """Decode a QR code from a file path, raw image bytes, or PIL Image.

    Returns a structured ScanResult or None if no valid barcode was found
    or if the input cannot be processed as an image.
    """
    img: Image.Image | None = None
    try:
        if isinstance(source, Image.Image):
            img = source
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                return None
            img = Image.open(path)
        elif isinstance(source, (bytes, bytearray)):
            img = Image.open(io.BytesIO(source))
        else:
            return None

        # Convert palette or problematic image modes to RGB/RGBA if necessary
        if img.mode not in ("L", "RGB", "RGBA"):
            img = img.convert("RGBA")

        results = zxingcpp.read_barcodes(img)
        if not results:
            return None

        # Take first detected barcode text and parse payload
        raw_text = results[0].text
        if not raw_text:
            return None

        return parse_payload(raw_text)

    except (UnidentifiedImageError, OSError, ValueError):
        return None
