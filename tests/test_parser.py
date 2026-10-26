from src.core.parser import (
    PayloadType,
    WifiConfig,
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
