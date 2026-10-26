import io
import zipfile

import zxingcpp
from PIL import Image

from src.core.batch_processor import (
    BatchItem,
    generate_batch_pdf_sheet,
    generate_batch_zip,
    parse_batch_file,
    parse_batch_text,
)


def test_parse_batch_text_plain_urls():
    text = """
    https://example.com/one
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    https://youtu.be/abc123xyz
    """
    items = parse_batch_text(text)
    assert len(items) == 3
    assert items[0].payload == "https://example.com/one"
    assert items[1].payload == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert "dQw4w9WgXcQ" in items[1].label or "youtube" in items[1].label.lower()
    assert items[2].payload == "https://youtu.be/abc123xyz"


def test_parse_batch_text_csv_delimiters():
    # Semicolon separated (German Excel style)
    text_semicolon = """
    Inhalt;Beschriftung
    https://py-qr.org;Offizielle Webseite
    "WIFI:S:Guest;;";Gäste-WLAN
    """
    items = parse_batch_text(text_semicolon)
    assert len(items) == 2
    assert items[0].payload == "https://py-qr.org"
    assert items[0].label == "Offizielle Webseite"
    assert items[1].payload == "WIFI:S:Guest;;"
    assert items[1].label == "Gäste-WLAN"

    # Tab separated
    text_tab = "https://example.com/1\tItem One\nhttps://example.com/2\tItem Two"
    items_tab = parse_batch_text(text_tab)
    assert len(items_tab) == 2
    assert items_tab[0].label == "Item One"


def test_parse_batch_file(tmp_path):
    csv_file = tmp_path / "test_import.csv"
    csv_file.write_text("https://a.com,Label A\nhttps://b.com,Label B\n", encoding="utf-8")
    items = parse_batch_file(csv_file)
    assert len(items) == 2
    assert items[0].payload == "https://a.com"
    assert items[0].label == "Label A"


def test_generate_batch_zip_png(tmp_path):
    items = [
        BatchItem(payload="https://example.com/1", label="First Item"),
        BatchItem(payload="https://www.youtube.com/watch?v=test123", label="YouTube Video"),
    ]
    zip_path = tmp_path / "output.zip"
    count = generate_batch_zip(
        items=items,
        target_zip_path=zip_path,
        format_type="png",
        shape="rounded",
        finder_color="#2563eb",
    )
    assert count == 2
    assert zip_path.exists()
    assert zip_path.stat().st_size > 200

    # Inspect zip contents
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        # Extract and verify decode with zxingcpp
        png_data = zf.read(namelist[0])
        img = Image.open(io.BytesIO(png_data))
        results = zxingcpp.read_barcodes(img)
        assert len(results) == 1
        assert results[0].text == "https://example.com/1"


def test_generate_batch_zip_svg(tmp_path):
    items = [
        BatchItem(payload="https://example.com/svg1", label="SVG One"),
        BatchItem(payload="https://example.com/svg2", label="SVG Two"),
    ]
    zip_path = tmp_path / "output_svg.zip"
    count = generate_batch_zip(
        items=items,
        target_zip_path=zip_path,
        format_type="svg",
        shape="dot",
        finder_color="#dc2626",
    )
    assert count == 2
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert len(zf.namelist()) == 2
        content = zf.read(zf.namelist()[0]).decode("utf-8")
        assert "<svg" in content
        assert "<circle" in content


def test_generate_batch_pdf_sheet(qapp, tmp_path):
    # 26 items to test multi-page (24 labels per page)
    items = [
        BatchItem(payload=f"https://example.com/item/{i}", label=f"Item #{i}") for i in range(1, 27)
    ]
    pdf_path = tmp_path / "sheet.pdf"
    count = generate_batch_pdf_sheet(
        items=items,
        target_pdf_path=pdf_path,
        layout="24_labels",
        dark_color="#1e293b",
        shape="rounded",
    )
    assert count == 26
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
