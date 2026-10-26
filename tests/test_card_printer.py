from PIL import Image

from src.core.card_printer import (
    CardConfig,
    render_card_to_image,
    render_card_to_pdf,
    render_card_to_png,
)


def test_render_card_to_image(qapp):
    config = CardConfig(
        title="Willkommen im Gäste-WLAN",
        subtitle="Einfach mit dem Smartphone verbinden",
        qr_data="WIFI:T:WPA;S:MusterNet;P:Geheim123;;",
        info_items=[("Netzwerk (SSID)", "MusterNet"), ("WLAN-Passwort", "Geheim123")],
        footer="py-qr Print Studio",
        page_size="A6",
    )
    img = render_card_to_image(config, dpi=150)
    assert not img.isNull()
    assert img.width() > 500
    assert img.height() > 700


def test_render_card_to_png(qapp, tmp_path):
    config = CardConfig(
        title="Konferenz-WLAN",
        subtitle="Verbindung ohne Passwort",
        qr_data="WIFI:S:Konferenz;T:nopass;;",
        info_items=[("Netzwerk", "Konferenz"), ("Verschlüsselung", "Offen")],
        page_size="A6",
    )
    png_path = tmp_path / "wlan_card.png"
    render_card_to_png(config, png_path, dpi=150)

    assert png_path.exists()
    assert png_path.stat().st_size > 5000

    with Image.open(png_path) as pil_img:
        assert pil_img.format == "PNG"
        assert pil_img.width > 500
        assert pil_img.height > 700


def test_render_card_to_pdf(qapp, tmp_path):
    config = CardConfig(
        title="Firmen-Kontaktkarte",
        subtitle="Scanne für Kontaktdaten",
        qr_data="BEGIN:VCARD\nVERSION:3.0\nFN:Max Mustermann\nEND:VCARD",
        info_items=[("Name", "Max Mustermann"), ("Telefon", "+49 123 456789")],
        page_size="A6",
    )
    pdf_path = tmp_path / "card.pdf"
    render_card_to_pdf(config, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000

    content = pdf_path.read_bytes()
    assert content.startswith(b"%PDF-")
