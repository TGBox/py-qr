"""Card printer module for generating printable WiFi and info stands as PDF and PNG."""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import segno
from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
    QPen,
)


@dataclass
class CardConfig:
    """Configuration for printable table stand or card."""

    title: str = "Willkommen im Gäste-WLAN"
    subtitle: str = "Scanne den QR-Code mit deiner Smartphone-Kamera"
    qr_data: str = ""
    info_items: list[tuple[str, str]] = field(default_factory=list)
    footer: str = "Schnell & sicher verbunden"
    page_size: Literal["A6", "A4"] = "A6"
    dark_color: str = "#000000"
    light_color: str = "#ffffff"


def _get_pixel_dimensions(page_size: str, dpi: int) -> tuple[int, int]:
    """Return (width_px, height_px) for given page size and DPI in portrait mode."""
    # A6 = 105 x 148 mm, A4 = 210 x 297 mm
    mm_w, mm_h = (105.0, 148.0) if page_size.upper() == "A6" else (210.0, 297.0)
    w_px = round(mm_w / 25.4 * dpi)
    h_px = round(mm_h / 25.4 * dpi)
    return w_px, h_px


def _generate_qr_image(data: str, dark_color: str, light_color: str) -> QImage:
    """Generate high-resolution QImage of QR code using segno."""
    qr = segno.make(data or "https://py-qr.local", error="h")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=16, border=1, dark=dark_color, light=light_color)
    img = QImage()
    img.loadFromData(buf.getvalue(), "PNG")
    return img


def draw_card(
    painter: QPainter,
    width: int,
    height: int,
    config: CardConfig,
    qr_image: QImage,
) -> None:
    """Draw professional card layout onto the given painter device."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # 1. Background
    painter.fillRect(0, 0, width, height, QColor("#ffffff"))

    margin_x = int(width * 0.07)
    margin_y = int(height * 0.05)

    # 2. Outer decorative border
    outer_border_pen = QPen(QColor("#cbd5e1"), max(1, int(width * 0.003)))
    painter.setPen(outer_border_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(
        QRectF(margin_x * 0.5, margin_y * 0.5, width - margin_x, height - margin_y),
        16,
        16,
    )

    cursor_y = float(margin_y * 1.4)

    # 3. Header Title
    title_font_size = max(12, int(height * 0.038))
    title_font = QFont("Segoe UI", title_font_size, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor("#0f172a"))
    title_rect = QRectF(margin_x, cursor_y, width - 2 * margin_x, height * 0.07)
    painter.drawText(
        title_rect,
        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        config.title,
    )
    cursor_y += title_rect.height() * 0.85

    # 4. Subtitle
    if config.subtitle:
        sub_font_size = max(9, int(height * 0.018))
        sub_font = QFont("Segoe UI", sub_font_size)
        painter.setFont(sub_font)
        painter.setPen(QColor("#64748b"))
        sub_rect = QRectF(margin_x, cursor_y, width - 2 * margin_x, height * 0.04)
        painter.drawText(
            sub_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            config.subtitle,
        )
        cursor_y += sub_rect.height()

    cursor_y += height * 0.015

    # 5. QR Code in Center
    qr_side = min(int(width * 0.52), int(height * 0.36))
    qr_x = (width - qr_side) // 2
    qr_rect = QRectF(qr_x, cursor_y, qr_side, qr_side)

    # QR Card Backdrop
    frame_pen = QPen(QColor("#e2e8f0"), 1)
    painter.setPen(frame_pen)
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(qr_rect.adjusted(-8, -8, 8, 8), 12, 12)

    painter.drawImage(qr_rect, qr_image)
    cursor_y += qr_side + height * 0.035

    # 6. Info Box (Details)
    if config.info_items:
        box_width = int(width * 0.82)
        box_x = (width - box_width) // 2
        item_h = int(height * 0.042)
        box_h = item_h * len(config.info_items) + int(height * 0.02)
        box_rect = QRectF(box_x, cursor_y, box_width, box_h)

        # Box background
        painter.setPen(QPen(QColor("#e2e8f0"), 1))
        painter.setBrush(QColor("#f8fafc"))
        painter.drawRoundedRect(box_rect, 10, 10)

        item_y = cursor_y + (height * 0.01)
        font_label = QFont("Segoe UI", max(9, int(height * 0.016)))
        font_val = QFont("Segoe UI", max(9, int(height * 0.017)), QFont.Weight.DemiBold)

        for label, val in config.info_items:
            # Label (left side)
            painter.setFont(font_label)
            painter.setPen(QColor("#64748b"))
            left_rect = QRectF(box_x + 16, item_y, box_width * 0.42, item_h)
            painter.drawText(
                left_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label + ":",
            )

            # Value (right side)
            painter.setFont(font_val)
            painter.setPen(QColor("#0f172a"))
            right_rect = QRectF(
                box_x + box_width * 0.44,
                item_y,
                box_width * 0.52,
                item_h,
            )
            painter.drawText(
                right_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                val,
            )

            item_y += item_h

    # 7. Footer
    if config.footer:
        footer_font = QFont("Segoe UI", max(8, int(height * 0.014)))
        painter.setFont(footer_font)
        painter.setPen(QColor("#94a3b8"))
        footer_rect = QRectF(margin_x, height - margin_y * 1.5, width - 2 * margin_x, margin_y)
        painter.drawText(
            footer_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            config.footer,
        )


def render_card_to_image(config: CardConfig, dpi: int = 300) -> QImage:
    """Render the card to a QImage at specified DPI."""
    width, height = _get_pixel_dimensions(config.page_size, dpi)
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.setDotsPerMeterX(int(dpi / 0.0254))
    image.setDotsPerMeterY(int(dpi / 0.0254))

    qr_img = _generate_qr_image(config.qr_data, config.dark_color, config.light_color)

    painter = QPainter(image)
    try:
        draw_card(painter, width, height, config, qr_img)
    finally:
        painter.end()

    return image


def render_card_to_png(config: CardConfig, target_path: Path, dpi: int = 300) -> None:
    """Render and save card as a high-resolution PNG file."""
    image = render_card_to_image(config, dpi=dpi)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(target_path), "PNG")


def render_card_to_pdf(config: CardConfig, target_path: Path) -> None:
    """Render and save card as a vector PDF document."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    writer = QPdfWriter(str(target_path))

    page_size_id = (
        QPageSize.PageSizeId.A6 if config.page_size.upper() == "A6" else QPageSize.PageSizeId.A4
    )
    writer.setPageSize(QPageSize(page_size_id))
    writer.setPageOrientation(QPageLayout.Orientation.Portrait)
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    writer.setResolution(300)

    width, height = _get_pixel_dimensions(config.page_size, dpi=300)
    qr_img = _generate_qr_image(config.qr_data, config.dark_color, config.light_color)

    painter = QPainter(writer)
    try:
        draw_card(painter, width, height, config, qr_img)
    finally:
        painter.end()
