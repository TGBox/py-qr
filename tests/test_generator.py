import tempfile
from pathlib import Path

from src.core.generator import (
    generate_qr_png_bytes,
    generate_qr_svg,
    save_qr_code,
)


def test_generate_qr_png_bytes():
    png_bytes = generate_qr_png_bytes("https://example.com", error_level="m")
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 50
    # PNG signature check
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_svg():
    svg_str = generate_qr_svg("Test Data", error_level="q", dark_color="#123456")
    assert isinstance(svg_str, str)
    assert "<svg" in svg_str
    assert 'stroke="#123456"' in svg_str


def test_save_qr_code_png():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "output.png"
        save_qr_code("Save Test", target, error_level="h")
        assert target.exists()
        assert target.stat().st_size > 50


def test_save_qr_code_svg():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "output.svg"
        save_qr_code("Save Test SVG", target, error_level="l")
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "<svg" in content
