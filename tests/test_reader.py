import io
import tempfile
from pathlib import Path

from PIL import Image

from src.core.generator import generate_qr_png_bytes, save_qr_code
from src.core.parser import PayloadType
from src.core.reader import decode_image


def test_decode_from_bytes():
    png_bytes = generate_qr_png_bytes("https://github.com/TGBox")
    result = decode_image(png_bytes)
    assert result is not None
    assert result.payload_type == PayloadType.URL
    assert result.raw_text == "https://github.com/TGBox"


def test_decode_from_pil_image():
    png_bytes = generate_qr_png_bytes("WIFI:T:WPA;S:HomeNetwork;P:SecretKey;;")
    img = Image.open(io.BytesIO(png_bytes))
    result = decode_image(img)
    assert result is not None
    assert result.payload_type == PayloadType.WIFI
    assert result.wifi_config is not None
    assert result.wifi_config.ssid == "HomeNetwork"
    assert result.wifi_config.password == "SecretKey"


def test_decode_from_file_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_qr.png"
        save_qr_code("Plain text scan", target)
        result = decode_image(target)
        assert result is not None
        assert result.payload_type == PayloadType.TEXT
        assert result.raw_text == "Plain text scan"


def test_decode_non_qr_image():
    # Blank white image with no QR code
    img = Image.new("RGB", (200, 200), color="white")
    result = decode_image(img)
    assert result is None


def test_decode_corrupt_data():
    corrupt_bytes = b"not an image at all"
    result = decode_image(corrupt_bytes)
    assert result is None
