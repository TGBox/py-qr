"""QR code generation module using segno."""

import io
from pathlib import Path

import segno


def generate_qr_png_bytes(
    data: str,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
) -> bytes:
    """Generate PNG bytes from QR data."""
    qr = segno.make(data, error=error_level.lower())
    buf = io.BytesIO()
    qr.save(
        buf,
        kind="png",
        scale=scale,
        border=border,
        dark=dark_color,
        light=light_color,
    )
    return buf.getvalue()


def generate_qr_svg(
    data: str,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
) -> str:
    """Generate SVG markup string from QR data."""
    qr = segno.make(data, error=error_level.lower())
    buf = io.BytesIO()
    qr.save(
        buf,
        kind="svg",
        scale=scale,
        border=border,
        dark=dark_color,
        light=light_color,
    )
    return buf.getvalue().decode("utf-8")


def save_qr_code(
    data: str,
    target_path: Path,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
) -> None:
    """Save QR code directly to target file path (PNG or SVG)."""
    qr = segno.make(data, error=error_level.lower())
    kind = target_path.suffix.lstrip(".").lower()
    if kind not in ("png", "svg", "pdf", "eps"):
        kind = "png"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    qr.save(
        target_path,
        kind=kind,
        scale=scale,
        border=border,
        dark=dark_color,
        light=light_color,
    )
