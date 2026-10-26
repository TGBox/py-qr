"""Payload parser and formatter for QR code contents."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PayloadType(str, Enum):
    """Supported payload types for decoded QR codes."""

    TEXT = "text"
    URL = "url"
    WIFI = "wifi"


@dataclass
class WifiConfig:
    """Structured WiFi configuration."""

    ssid: str
    password: str = ""
    security: str = "WPA"  # WPA, WEP, nopass
    hidden: bool = False


@dataclass
class ScanResult:
    """Represents a decoded and categorized QR code result."""

    raw_text: str
    payload_type: PayloadType
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)
    wifi_config: WifiConfig | None = None
    url: str | None = None


def escape_wifi_string(value: str) -> str:
    """Escape special characters in WiFi QR payload strings."""
    escaped = value.replace("\\", r"\\")
    for char in [";", ",", ":", '"']:
        escaped = escaped.replace(char, "\\" + char)
    return escaped


def unescape_wifi_string(value: str) -> str:
    """Unescape special characters in WiFi QR payload strings."""
    return re.sub(r"\\([\\;,:\"])", r"\1", value)


def parse_wifi_fields(content: str) -> dict[str, str]:
    """Parse key-value pairs from a WiFi QR code payload."""
    fields: dict[str, str] = {}
    pattern = re.compile(r"([A-Z]):((?:\\.|[^;])*)")
    for match in pattern.finditer(content):
        key = match.group(1)
        val = match.group(2)
        fields[key] = unescape_wifi_string(val)
    return fields


def parse_payload(raw_text: str) -> ScanResult:
    """Analyze and parse raw decoded QR string into structured ScanResult."""
    text = raw_text.strip()

    # Check for WiFi code format: WIFI:S:...;...;;
    if text.upper().startswith("WIFI:"):
        wifi_body = text[5:]
        if wifi_body.endswith(";;"):
            wifi_body = wifi_body[:-2]
        elif wifi_body.endswith(";"):
            wifi_body = wifi_body[:-1]

        fields = parse_wifi_fields(wifi_body)
        ssid = fields.get("S", "")
        password = fields.get("P", "")
        security = fields.get("T", "WPA")
        hidden = fields.get("H", "").lower() in ("true", "1")

        wifi_config = WifiConfig(
            ssid=ssid,
            password=password,
            security=security,
            hidden=hidden,
        )

        title = f"WLAN: {ssid}" if ssid else "WLAN Konfiguration"
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.WIFI,
            title=title,
            metadata={"ssid": ssid, "security": security, "hidden": hidden},
            wifi_config=wifi_config,
        )

    # Check for Web URL
    url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    if url_pattern.match(text):
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.URL,
            title=text,
            url=text,
            metadata={"url": text},
        )

    # Fallback: Plain text
    preview = text[:40] + ("..." if len(text) > 40 else "")
    return ScanResult(
        raw_text=raw_text,
        payload_type=PayloadType.TEXT,
        title=preview or "Text",
        metadata={"length": len(raw_text)},
    )


def format_wifi_payload(config: WifiConfig) -> str:
    """Format WifiConfig into standard WIFI: QR code string."""
    escaped_ssid = escape_wifi_string(config.ssid)
    escaped_password = escape_wifi_string(config.password)
    hidden_str = "true" if config.hidden else "false"
    return f"WIFI:T:{config.security};S:{escaped_ssid};P:{escaped_password};H:{hidden_str};;"
