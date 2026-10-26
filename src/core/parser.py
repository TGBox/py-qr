"""Payload parser and formatter for QR code contents."""

import re
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PayloadType(str, Enum):
    """Supported payload types for decoded QR codes."""

    TEXT = "text"
    URL = "url"
    WIFI = "wifi"
    VCARD = "vcard"
    EMAIL = "email"
    GEO = "geo"


@dataclass
class WifiConfig:
    """Structured WiFi configuration."""

    ssid: str
    password: str = ""
    security: str = "WPA"  # WPA, WEP, nopass
    hidden: bool = False


@dataclass
class VCardConfig:
    """Structured contact card (vCard 3.0) configuration."""

    first_name: str = ""
    last_name: str = ""
    organization: str = ""
    phone: str = ""
    email: str = ""
    url: str = ""
    note: str = ""


@dataclass
class EmailConfig:
    """Structured email configuration."""

    to: str = ""
    subject: str = ""
    body: str = ""


@dataclass
class GeoConfig:
    """Structured geographic coordinate configuration."""

    latitude: float = 0.0
    longitude: float = 0.0
    query: str = ""


@dataclass
class ScanResult:
    """Represents a decoded and categorized QR code result."""

    raw_text: str
    payload_type: PayloadType
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)
    wifi_config: WifiConfig | None = None
    url: str | None = None
    vcard_config: VCardConfig | None = None
    email_config: EmailConfig | None = None
    geo_config: GeoConfig | None = None


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


def format_wifi_payload(config: WifiConfig) -> str:
    """Format WifiConfig into standard WIFI: QR code string."""
    escaped_ssid = escape_wifi_string(config.ssid)
    escaped_password = escape_wifi_string(config.password)
    hidden_str = "true" if config.hidden else "false"
    return f"WIFI:T:{config.security};S:{escaped_ssid};P:{escaped_password};H:{hidden_str};;"


def format_vcard_payload(config: VCardConfig) -> str:
    """Format VCardConfig into standard vCard 3.0 string."""
    full_name = f"{config.first_name} {config.last_name}".strip()
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{config.last_name};{config.first_name};;;",
        f"FN:{full_name}",
    ]
    if config.organization:
        lines.append(f"ORG:{config.organization}")
    if config.phone:
        lines.append(f"TEL;TYPE=CELL:{config.phone}")
    if config.email:
        lines.append(f"EMAIL:{config.email}")
    if config.url:
        lines.append(f"URL:{config.url}")
    if config.note:
        lines.append(f"NOTE:{config.note}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def parse_vcard_payload(text: str) -> VCardConfig:
    """Extract fields from a vCard formatted string."""
    first_name = ""
    last_name = ""
    org = ""
    phone = ""
    email = ""
    url = ""
    note = ""

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key_upper = key.upper()

        if key_upper == "N":
            parts = value.split(";")
            last_name = parts[0] if len(parts) > 0 else ""
            first_name = parts[1] if len(parts) > 1 else ""
        elif key_upper == "FN" and not first_name and not last_name:
            parts = value.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
        elif key_upper.startswith("ORG"):
            org = value
        elif key_upper.startswith("TEL"):
            phone = value
        elif key_upper.startswith("EMAIL"):
            email = value
        elif key_upper.startswith("URL"):
            url = value
        elif key_upper.startswith("NOTE"):
            note = value

    return VCardConfig(
        first_name=first_name,
        last_name=last_name,
        organization=org,
        phone=phone,
        email=email,
        url=url,
        note=note,
    )


def format_email_payload(config: EmailConfig) -> str:
    """Format EmailConfig into standard mailto URI."""
    params = []
    if config.subject:
        params.append(f"subject={urllib.parse.quote(config.subject)}")
    if config.body:
        params.append(f"body={urllib.parse.quote(config.body)}")
    query = f"?{'&'.join(params)}" if params else ""
    return f"mailto:{config.to}{query}"


def parse_email_payload(text: str) -> EmailConfig:
    """Extract fields from mailto or MATMSG payload."""
    if text.lower().startswith("mailto:"):
        parsed = urllib.parse.urlparse(text)
        to_addr = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        subject = qs.get("subject", [""])[0]
        body = qs.get("body", [""])[0]
        return EmailConfig(to=to_addr, subject=subject, body=body)

    if text.upper().startswith("MATMSG:"):
        # Format: MATMSG:TO:test@example.com;SUB:Subject;BODY:Hello;;
        body_content = text[7:]
        to_match = re.search(r"TO:([^;]+);", body_content, re.IGNORECASE)
        sub_match = re.search(r"SUB:([^;]+);", body_content, re.IGNORECASE)
        msg_match = re.search(r"BODY:([^;]+);", body_content, re.IGNORECASE)
        return EmailConfig(
            to=to_match.group(1) if to_match else "",
            subject=sub_match.group(1) if sub_match else "",
            body=msg_match.group(1) if msg_match else "",
        )

    return EmailConfig(to=text)


def format_geo_payload(config: GeoConfig) -> str:
    """Format GeoConfig into standard geo URI."""
    base = f"geo:{config.latitude:.6g},{config.longitude:.6g}"
    if config.query:
        base += f"?q={urllib.parse.quote(config.query)}"
    return base


def parse_geo_payload(text: str) -> GeoConfig:
    """Extract coordinates and query from geo URI."""
    # Format: geo:52.5200,13.4050?q=Berlin
    body = text[4:]
    query = ""
    if "?q=" in body:
        coords_part, query_part = body.split("?q=", 1)
        query = urllib.parse.unquote(query_part)
    else:
        coords_part = body

    lat, lon = 0.0, 0.0
    if "," in coords_part:
        parts = coords_part.split(",")
        try:
            lat = float(parts[0])
            lon = float(parts[1])
        except ValueError:
            pass

    return GeoConfig(latitude=lat, longitude=lon, query=query)


def parse_payload(raw_text: str) -> ScanResult:
    """Analyze and parse raw decoded QR string into structured ScanResult."""
    text = raw_text.strip()

    # 1. WiFi format: WIFI:S:...;...;;
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

    # 2. Contact card: BEGIN:VCARD
    if text.upper().startswith("BEGIN:VCARD"):
        vcard_config = parse_vcard_payload(text)
        name_parts = [vcard_config.first_name, vcard_config.last_name]
        full_name = " ".join(p for p in name_parts if p).strip()
        title = f"Kontakt: {full_name}" if full_name else "Visitenkarte (vCard)"
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.VCARD,
            title=title,
            metadata={
                "name": full_name,
                "phone": vcard_config.phone,
                "email": vcard_config.email,
                "organization": vcard_config.organization,
            },
            vcard_config=vcard_config,
        )

    # 3. Email: mailto: or MATMSG:
    if text.lower().startswith("mailto:") or text.upper().startswith("MATMSG:"):
        email_config = parse_email_payload(text)
        title = f"E-Mail an: {email_config.to}" if email_config.to else "E-Mail Entwurf"
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.EMAIL,
            title=title,
            metadata={
                "to": email_config.to,
                "subject": email_config.subject,
            },
            email_config=email_config,
        )

    # 4. Geo coordinate: geo:
    if text.lower().startswith("geo:"):
        geo_config = parse_geo_payload(text)
        loc_str = f"{geo_config.latitude:.4f}, {geo_config.longitude:.4f}"
        title = (
            f"Standort: {geo_config.query} ({loc_str})"
            if geo_config.query
            else f"Standort: {loc_str}"
        )
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.GEO,
            title=title,
            metadata={
                "latitude": geo_config.latitude,
                "longitude": geo_config.longitude,
                "query": geo_config.query,
            },
            geo_config=geo_config,
        )

    # 5. Web URL
    url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    if url_pattern.match(text):
        return ScanResult(
            raw_text=raw_text,
            payload_type=PayloadType.URL,
            title=text,
            url=text,
            metadata={"url": text},
        )

    # 6. Fallback: Plain text
    preview = text[:40] + ("..." if len(text) > 40 else "")
    return ScanResult(
        raw_text=raw_text,
        payload_type=PayloadType.TEXT,
        title=preview or "Text",
        metadata={"length": len(raw_text)},
    )
