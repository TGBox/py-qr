import io
import tempfile
from pathlib import Path

import zxingcpp
from PIL import Image, ImageDraw

from src.core.generator import (
    create_preset_icon_image,
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


def test_generate_artistic_shapes_decode():
    for shape in ("square", "dot", "rounded"):
        png_bytes = generate_qr_png_bytes(
            "https://py-qr.local/shape-test",
            shape=shape,  # type: ignore[arg-type]
            dark_color="#1e293b",
            finder_color="#e11d48",
        )
        img = Image.open(io.BytesIO(png_bytes))
        results = zxingcpp.read_barcodes(img)
        assert len(results) == 1
        assert results[0].text == "https://py-qr.local/shape-test"


def test_generate_artistic_preset_icons_decode():
    for icon in ("wifi", "contact", "email", "url", "star"):
        png_bytes = generate_qr_png_bytes(
            "https://py-qr.local/icon-test",
            shape="rounded",
            dark_color="#0f172a",
            finder_color="#2563eb",
            logo_icon=icon,
        )
        img = Image.open(io.BytesIO(png_bytes))
        results = zxingcpp.read_barcodes(img)
        assert len(results) == 1
        assert results[0].text == "https://py-qr.local/icon-test"


def test_generate_artistic_custom_logo_decode(tmp_path):
    logo_file = tmp_path / "custom_logo.png"
    logo_img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(logo_img)
    d.ellipse([2, 2, 46, 46], fill="#10b981")
    logo_img.save(logo_file)

    png_bytes = generate_qr_png_bytes(
        "https://py-qr.local/custom-logo",
        shape="dot",
        dark_color="#111827",
        finder_color="#10b981",
        logo_image_path=logo_file,
    )
    img = Image.open(io.BytesIO(png_bytes))
    results = zxingcpp.read_barcodes(img)
    assert len(results) == 1
    assert results[0].text == "https://py-qr.local/custom-logo"


def test_generate_qr_svg():
    svg_str = generate_qr_svg("Test Data", error_level="q", dark_color="#123456")
    assert isinstance(svg_str, str)
    assert "<svg" in svg_str
    assert 'stroke="#123456"' in svg_str


def test_generate_qr_svg_artistic():
    svg_str = generate_qr_svg(
        "Test Artistic SVG",
        shape="dot",
        finder_color="#ff0000",
        logo_icon="star",
    )
    assert "<svg" in svg_str
    assert "<circle" in svg_str
    assert 'fill="#ff0000"' in svg_str
    assert "<image" in svg_str


def test_create_preset_icon_image():
    for name in ("star", "email", "wifi", "url", "contact"):
        icon = create_preset_icon_image(name, size=64, color="#123456")
        assert icon.size == (64, 64)
        assert icon.mode == "RGBA"


def test_save_qr_code_png():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "output.png"
        save_qr_code(
            "Save Test",
            target,
            error_level="h",
            shape="rounded",
            finder_color="#2563eb",
            logo_icon="wifi",
        )
        assert target.exists()
        assert target.stat().st_size > 50


def test_save_qr_code_svg():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "output.svg"
        save_qr_code(
            "Save Test SVG",
            target,
            error_level="l",
            shape="dot",
            finder_color="#059669",
        )
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "<circle" in content
