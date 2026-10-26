from src.core.parser import (
    EmailConfig,
    GeoConfig,
    PayloadType,
    VCardConfig,
    WifiConfig,
    format_email_payload,
    format_geo_payload,
    format_vcard_payload,
    format_wifi_payload,
    parse_payload,
)


def test_parse_plain_text():
    result = parse_payload("Hallo Welt 123")
    assert result.payload_type == PayloadType.TEXT
    assert result.raw_text == "Hallo Welt 123"
    assert result.wifi_config is None
    assert result.url is None


def test_parse_url():
    result = parse_payload("https://github.com/TGBox/py-qr")
    assert result.payload_type == PayloadType.URL
    assert result.url == "https://github.com/TGBox/py-qr"

    http_result = parse_payload("http://example.com/test?q=1")
    assert http_result.payload_type == PayloadType.URL
    assert http_result.url == "http://example.com/test?q=1"


def test_parse_wifi_standard():
    raw = "WIFI:T:WPA;S:MyHomeWiFi;P:Secret123;H:false;;"
    result = parse_payload(raw)
    assert result.payload_type == PayloadType.WIFI
    assert result.wifi_config is not None
    assert result.wifi_config.ssid == "MyHomeWiFi"
    assert result.wifi_config.password == "Secret123"
    assert result.wifi_config.security == "WPA"
    assert result.wifi_config.hidden is False


def test_parse_wifi_open_network():
    raw = "WIFI:S:OpenGuest;T:nopass;;"
    result = parse_payload(raw)
    assert result.payload_type == PayloadType.WIFI
    assert result.wifi_config is not None
    assert result.wifi_config.ssid == "OpenGuest"
    assert result.wifi_config.password == ""
    assert result.wifi_config.security == "nopass"


def test_parse_wifi_escaped_characters():
    # Semicolons and colons can be escaped with backslash
    raw = r"WIFI:T:WPA;S:My\;Special\:WiFi;P:P\@ss\;word;;"
    result = parse_payload(raw)
    assert result.payload_type == PayloadType.WIFI
    assert result.wifi_config is not None
    assert result.wifi_config.ssid == "My;Special:WiFi"
    assert result.wifi_config.password == r"P\@ss;word"


def test_format_wifi_payload():
    config = WifiConfig(
        ssid="OfficeNet",
        password="SafePassword99",
        security="WPA",
        hidden=True,
    )
    formatted = format_wifi_payload(config)
    assert "S:OfficeNet" in formatted
    assert "P:SafePassword99" in formatted
    assert "T:WPA" in formatted
    assert "H:true" in formatted
    # Round-trip verification
    parsed = parse_payload(formatted)
    assert parsed.payload_type == PayloadType.WIFI
    assert parsed.wifi_config == config


def test_parse_vcard():
    raw = (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        "N:Mustermann;Max;;;\n"
        "FN:Max Mustermann\n"
        "ORG:Musterfirma GmbH\n"
        "TEL;TYPE=CELL:+49123456789\n"
        "EMAIL:max@example.com\n"
        "URL:https://example.com\n"
        "NOTE:Projektleiter\n"
        "END:VCARD"
    )
    result = parse_payload(raw)
    assert result.payload_type == PayloadType.VCARD
    assert result.vcard_config is not None
    assert result.vcard_config.first_name == "Max"
    assert result.vcard_config.last_name == "Mustermann"
    assert result.vcard_config.organization == "Musterfirma GmbH"
    assert result.vcard_config.phone == "+49123456789"
    assert result.vcard_config.email == "max@example.com"
    assert result.vcard_config.url == "https://example.com"
    assert result.vcard_config.note == "Projektleiter"


def test_format_vcard_payload():
    config = VCardConfig(
        first_name="Erika",
        last_name="Musterfrau",
        organization="Tech AG",
        phone="+49987654321",
        email="erika@tech.example",
        url="https://tech.example",
        note="Entwicklerin",
    )
    formatted = format_vcard_payload(config)
    assert "BEGIN:VCARD" in formatted
    assert "VERSION:3.0" in formatted
    assert "FN:Erika Musterfrau" in formatted
    assert "N:Musterfrau;Erika;;;" in formatted
    assert "ORG:Tech AG" in formatted
    assert "TEL;TYPE=CELL:+49987654321" in formatted
    assert "EMAIL:erika@tech.example" in formatted
    assert "END:VCARD" in formatted

    # Roundtrip
    parsed = parse_payload(formatted)
    assert parsed.payload_type == PayloadType.VCARD
    assert parsed.vcard_config == config


def test_parse_and_format_email():
    config = EmailConfig(
        to="kontakt@firma.de",
        subject="Anfrage Projekt",
        body="Hallo,\nich interessiere mich für Ihr Angebot.",
    )
    formatted = format_email_payload(config)
    assert formatted.startswith("mailto:kontakt@firma.de")
    assert "subject=" in formatted

    parsed = parse_payload(formatted)
    assert parsed.payload_type == PayloadType.EMAIL
    assert parsed.email_config is not None
    assert parsed.email_config.to == "kontakt@firma.de"
    assert parsed.email_config.subject == "Anfrage Projekt"
    assert "Angebot" in parsed.email_config.body


def test_parse_and_format_geo():
    config = GeoConfig(latitude=52.5200, longitude=13.4050, query="Berlin Fernsehturm")
    formatted = format_geo_payload(config)
    assert formatted.startswith("geo:52.52,13.405")

    parsed = parse_payload(formatted)
    assert parsed.payload_type == PayloadType.GEO
    assert parsed.geo_config is not None
    assert abs(parsed.geo_config.latitude - 52.52) < 0.001
    assert abs(parsed.geo_config.longitude - 13.405) < 0.001
