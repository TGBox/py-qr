"""Core batch processing module for multi-item QR code generation and export."""

import csv
import re
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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

from src.core.generator import generate_qr_png_bytes, generate_qr_svg


@dataclass
class BatchItem:
    """Represents a single entry in a batch queue."""

    payload: str
    label: str = ""
    filename: str = ""

    def get_effective_label(self, index: int = 1) -> str:
        """Return label or fallback name if label is empty."""
        if self.label.strip():
            return self.label.strip()
        # Fallback to smart identifier
        yt_id = extract_youtube_identifier(self.payload)
        if yt_id:
            return f"YouTube ({yt_id})"
        if self.payload.startswith(("http://", "https://")):
            # Domain or short url
            clean = re.sub(r"^https?://(www\.)?", "", self.payload).strip("/")
            return clean[:30]
        return f"QR-Code {index:02d}"


def sanitize_filename(name: str) -> str:
    """Sanitize string for use as safe filesystem name."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    clean = re.sub(r"\s+", "_", clean)
    return clean[:60] or "qr_item"


def extract_youtube_identifier(url: str) -> str | None:
    """Extract YouTube video ID or identifier from YouTube URL if present."""
    yt_match = re.search(r"(?:v=|\/embed\/|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{8,15})", url)
    if yt_match:
        return yt_match.group(1)
    return None


def parse_batch_text(text: str) -> list[BatchItem]:
    """Parse raw text, lines, or pasted CSV/TSV table into a list of BatchItems."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []

    # Detect delimiter
    sample = "\n".join(lines[:5])
    delimiter = ","
    if "\t" in sample:
        delimiter = "\t"
    elif ";" in sample:
        delimiter = ";"
    elif "|" in sample:
        delimiter = "|"

    items: list[BatchItem] = []
    reader = csv.reader(lines, delimiter=delimiter)

    first_row = True
    for row in reader:
        if not row:
            continue
        cleaned_cells = [cell.strip() for cell in row if cell.strip()]
        if not cleaned_cells:
            continue

        # Header detection
        if first_row:
            first_row = False
            first_lowered = [c.lower() for c in cleaned_cells]
            known_headers = {
                "inhalt",
                "payload",
                "url",
                "link",
                "text",
                "beschriftung",
                "label",
                "titel",
                "title",
                "name",
            }
            if any(h in known_headers for h in first_lowered):
                continue

        if len(cleaned_cells) == 1:
            val = cleaned_cells[0]
            yt = extract_youtube_identifier(val)
            label = f"YouTube {yt}" if yt else ""
            items.append(BatchItem(payload=val, label=label))
        else:
            # Check which column is the URL/payload
            cell0 = cleaned_cells[0]
            cell1 = cleaned_cells[1]
            if not cell0.startswith(
                ("http://", "https://", "WIFI:", "BEGIN:")
            ) and cell1.startswith(("http://", "https://", "WIFI:", "BEGIN:")):
                # Column 0 is label, Column 1 is payload
                items.append(BatchItem(payload=cell1, label=cell0))
            else:
                items.append(BatchItem(payload=cell0, label=cell1))

    return items


def parse_batch_file(path: Path) -> list[BatchItem]:
    """Read file with UTF-8 or CP1252 fallback and parse items."""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="cp1252", errors="replace")
    return parse_batch_text(content)


def generate_batch_zip(
    items: list[BatchItem],
    target_zip_path: Path,
    format_type: Literal["png", "svg"] = "png",
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    shape: str = "square",
    finder_color: str | None = None,
    logo_icon: str | None = None,
    logo_image_path: Path | str | None = None,
    progress_callback: Callable[[int, int], bool] | None = None,
) -> int:
    """Generate all items and save into a compressed ZIP file."""
    target_zip_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    total = len(items)

    with zipfile.ZipFile(target_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(items, start=1):
            if progress_callback and not progress_callback(idx - 1, total):
                break

            base_name = sanitize_filename(item.get_effective_label(idx))
            ext = "svg" if format_type.lower() == "svg" else "png"
            file_name = f"{idx:02d}_{base_name}.{ext}"

            if ext == "svg":
                svg_data = generate_qr_svg(
                    data=item.payload,
                    error_level=error_level,
                    dark_color=dark_color,
                    light_color=light_color,
                    scale=10,
                    shape=shape,  # type: ignore[arg-type]
                    finder_color=finder_color,
                    logo_icon=logo_icon,
                    logo_image_path=logo_image_path,
                )
                zf.writestr(file_name, svg_data.encode("utf-8"))
            else:
                png_bytes = generate_qr_png_bytes(
                    data=item.payload,
                    error_level=error_level,
                    dark_color=dark_color,
                    light_color=light_color,
                    scale=12,
                    shape=shape,  # type: ignore[arg-type]
                    finder_color=finder_color,
                    logo_icon=logo_icon,
                    logo_image_path=logo_image_path,
                )
                zf.writestr(file_name, png_bytes)

            count += 1

    if progress_callback:
        progress_callback(count, total)

    return count


def generate_batch_pdf_sheet(
    items: list[BatchItem],
    target_pdf_path: Path,
    layout: Literal["24_labels", "8_cards"] = "24_labels",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    shape: str = "square",
    finder_color: str | None = None,
    logo_icon: str | None = None,
    logo_image_path: Path | str | None = None,
    progress_callback: Callable[[int, int], bool] | None = None,
) -> int:
    """Generate print-ready multi-page DIN A4 PDF sheet with QR code grid."""
    target_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    writer = QPdfWriter(str(target_pdf_path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageOrientation(QPageLayout.Orientation.Portrait)
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    writer.setResolution(300)

    # DIN A4 portrait at 300 DPI: 210 x 297 mm
    page_w = round(210.0 / 25.4 * 300)
    page_h = round(297.0 / 25.4 * 300)

    cols, rows = (3, 8) if layout == "24_labels" else (2, 4)
    per_page = cols * rows

    margin_x = int(page_w * 0.05)
    margin_y = int(page_h * 0.04)
    grid_w = page_w - 2 * margin_x
    grid_h = page_h - 2 * margin_y

    cell_w = grid_w / cols
    cell_h = grid_h / rows

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    total = len(items)
    count = 0

    try:
        for idx, item in enumerate(items):
            if progress_callback and not progress_callback(idx, total):
                break

            idx_on_page = idx % per_page
            if idx > 0 and idx_on_page == 0:
                writer.newPage()

            col = idx_on_page % cols
            row = idx_on_page // cols

            x0 = margin_x + col * cell_w
            y0 = margin_y + row * cell_h

            # Generate QR Image
            png_bytes = generate_qr_png_bytes(
                data=item.payload,
                error_level="h",
                dark_color=dark_color,
                light_color=light_color,
                scale=8,
                border=1,
                shape=shape,  # type: ignore[arg-type]
                finder_color=finder_color,
                logo_icon=logo_icon,
                logo_image_path=logo_image_path,
            )
            qr_img = QImage()
            qr_img.loadFromData(png_bytes, "PNG")

            # Draw subtle cutting guide border
            painter.setPen(QPen(QColor("#e2e8f0"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(x0, y0, cell_w, cell_h))

            # Inner padding
            pad_x = cell_w * 0.08
            pad_y = cell_h * 0.08

            # QR Code sizing inside cell
            qr_max_size = min(cell_w - 2 * pad_x, cell_h * 0.72)
            qr_x = x0 + (cell_w - qr_max_size) / 2.0
            qr_y = y0 + pad_y

            painter.drawImage(
                QRectF(qr_x, qr_y, qr_max_size, qr_max_size),
                qr_img,
            )

            # Label text
            label_text = item.get_effective_label(idx + 1)
            font_size = max(7, int(cell_h * 0.065))
            painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
            painter.setPen(QColor("#0f172a"))

            label_rect = QRectF(
                x0 + pad_x,
                qr_y + qr_max_size + 4,
                cell_w - 2 * pad_x,
                cell_h - qr_max_size - pad_y - 8,
            )
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                label_text,
            )

            count += 1
    finally:
        painter.end()

    if progress_callback:
        progress_callback(count, total)

    return count
