from src.core.generator import generate_qr_png_bytes
from src.core.parser import ScanResult
from src.gui.workers import DecodeWorker, GenerateWorker


def test_decode_worker_success(qtbot):
    png_bytes = generate_qr_png_bytes("https://github.com")
    worker = DecodeWorker(png_bytes)

    with qtbot.waitSignal(worker.success, timeout=2000) as blocker:
        worker.start()

    result = blocker.args[0]
    assert isinstance(result, ScanResult)
    assert result.raw_text == "https://github.com"


def test_decode_worker_failed(qtbot):
    corrupt_data = b"empty or corrupt"
    worker = DecodeWorker(corrupt_data)

    with qtbot.waitSignal(worker.failed, timeout=2000) as blocker:
        worker.start()

    error_msg = blocker.args[0]
    assert isinstance(error_msg, str)
    assert "Kein QR-Code" in error_msg or "Fehler" in error_msg


def test_generate_worker_success(qtbot):
    worker = GenerateWorker(
        data="https://example.com",
        error_level="m",
        dark_color="#000000",
        light_color="#ffffff",
        scale=5,
    )

    with qtbot.waitSignal(worker.success, timeout=2000) as blocker:
        worker.start()

    png_bytes = blocker.args[0]
    assert isinstance(png_bytes, bytes)
    assert png_bytes.startswith(b"\x89PNG")
