"""QR code generation module using segno and Pillow for artistic styles."""

import base64
import io
import math
from pathlib import Path
from typing import Literal

import segno
from PIL import Image, ImageDraw

ShapeType = Literal["square", "dot", "rounded"]


def is_finder_module(r: int, c: int, matrix_size: int) -> bool:
    """Return True if (r, c) module belongs to one of the three 7x7 corner finder patterns."""
    return (r < 7 and c < 7) or (r < 7 and c >= matrix_size - 7) or (r >= matrix_size - 7 and c < 7)


def create_preset_icon_image(name: str, size: int, color: str = "#000000") -> Image.Image:
    """Draw a clean, crisp vector-like preset icon using Pillow on a transparent canvas."""
    icon_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon_img)
    pad = size * 0.15
    w = size - 2 * pad
    h = size - 2 * pad
    cx = size / 2
    cy = size / 2

    name_clean = name.lower().strip()

    if name_clean == "star":
        points: list[tuple[float, float]] = []
        outer_r = w / 2
        inner_r = outer_r * 0.42
        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            angle = -math.pi / 2 + i * math.pi / 5
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        d.polygon(points, fill=color)

    elif name_clean == "email":
        x0, y0, x1, y1 = pad, pad + h * 0.15, pad + w, pad + h * 0.85
        d.rounded_rectangle([x0, y0, x1, y1], radius=max(2, int(size * 0.08)), fill=color)
        flap = [(x0 + 3, y0 + 3), (cx, cy + h * 0.12), (x1 - 3, y0 + 3)]
        d.line(flap, fill="#ffffff", width=max(2, int(size * 0.06)))

    elif name_clean in ("contact", "vcard"):
        head_r = w * 0.22
        d.ellipse(
            [cx - head_r, pad + h * 0.04, cx + head_r, pad + h * 0.04 + 2 * head_r], fill=color
        )
        body_top = pad + h * 0.52
        d.chord(
            [cx - w * 0.45, body_top, cx + w * 0.45, pad + h * 1.18], start=180, end=360, fill=color
        )

    elif name_clean == "wifi":
        dot_r = max(2, int(size * 0.07))
        d.ellipse([cx - dot_r, cy + h * 0.3 - dot_r, cx + dot_r, cy + h * 0.3 + dot_r], fill=color)
        for r_factor in [0.26, 0.42]:
            r = w * r_factor
            d.arc(
                [cx - r, cy + h * 0.3 - r, cx + r, cy + h * 0.3 + r],
                start=215,
                end=325,
                fill=color,
                width=max(2, int(size * 0.07)),
            )

    elif name_clean == "url":
        r = w * 0.44
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, int(size * 0.06)))
        d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=max(2, int(size * 0.05)))
        d.ellipse(
            [cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
            outline=color,
            width=max(2, int(size * 0.05)),
        )

    return icon_img


def generate_qr_png_bytes(
    data: str,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
    shape: ShapeType = "square",
    finder_color: str | None = None,
    logo_icon: str | None = None,
    logo_image_path: Path | str | None = None,
) -> bytes:
    """Generate PNG bytes from QR data with optional artistic shapes and central emblem."""
    # When logo is provided, elevate error correction level to 'h' (30%) to ensure scanability
    effective_err = "h" if (logo_icon or logo_image_path) else error_level.lower()
    qr = segno.make(data, error=effective_err)

    # Fast path for classic standard square code without custom eye color or logo
    if shape == "square" and not finder_color and not logo_icon and not logo_image_path:
        buf = io.BytesIO()
        qr.save(
            buf,
            kind="png",
            scale=scale,
            border=border,
            dark=dark_color,
            light=light_color,
        )
        return buf.getvalue()

    # Custom artistic rendering with Pillow
    matrix = qr.matrix
    matrix_size = len(matrix)
    total_dim = (matrix_size + 2 * border) * scale

    img = Image.new("RGBA", (total_dim, total_dim), light_color)
    draw = ImageDraw.Draw(img)

    f_color = finder_color or dark_color

    for r in range(matrix_size):
        for c in range(matrix_size):
            if not matrix[r][c]:
                continue
            x1 = (c + border) * scale
            y1 = (r + border) * scale
            x2 = x1 + scale
            y2 = y1 + scale

            # Keep corner finder pattern modules solid for maximum scanner compatibility
            if is_finder_module(r, c, matrix_size):
                draw.rectangle([x1, y1, x2, y2], fill=f_color)
            else:
                if shape == "dot":
                    margin = scale * 0.08
                    draw.ellipse(
                        [x1 + margin, y1 + margin, x2 - margin, y2 - margin], fill=dark_color
                    )
                elif shape == "rounded":
                    rad = max(2, int(scale * 0.35))
                    draw.rounded_rectangle([x1, y1, x2, y2], radius=rad, fill=dark_color)
                else:
                    draw.rectangle([x1, y1, x2, y2], fill=dark_color)

    # Embed central emblem if requested
    if logo_icon or logo_image_path:
        logo_size = int(total_dim * 0.22)
        cx = total_dim // 2
        cy = total_dim // 2
        logo_x = cx - logo_size // 2
        logo_y = cy - logo_size // 2

        # Protective background pad in light color
        pad = max(4, int(scale * 0.5))
        draw.rounded_rectangle(
            [logo_x - pad, logo_y - pad, logo_x + logo_size + pad, logo_y + logo_size + pad],
            radius=int(logo_size * 0.25),
            fill=light_color,
        )

        if logo_image_path and Path(logo_image_path).is_file():
            try:
                custom_img = Image.open(logo_image_path).convert("RGBA")
                custom_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
                paste_x = cx - custom_img.width // 2
                paste_y = cy - custom_img.height // 2
                img.alpha_composite(custom_img, (paste_x, paste_y))
            except (OSError, ValueError):
                pass
        elif logo_icon:
            icon_img = create_preset_icon_image(logo_icon, logo_size, color=f_color)
            img.alpha_composite(icon_img, (logo_x, logo_y))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_svg(
    data: str,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
    shape: ShapeType = "square",
    finder_color: str | None = None,
    logo_icon: str | None = None,
    logo_image_path: Path | str | None = None,
) -> str:
    """Generate SVG markup string from QR data with optional artistic styling."""
    effective_err = "h" if (logo_icon or logo_image_path) else error_level.lower()
    qr = segno.make(data, error=effective_err)

    if shape == "square" and not finder_color and not logo_icon and not logo_image_path:
        buf = io.BytesIO()
        qr.save(
            buf,
            kind="svg",
            scale=scale,
            border=border,
            dark=dark_color,
            light=light_color,
        )
        return buf.getvalue().decode("utf-8")

    matrix = qr.matrix
    matrix_size = len(matrix)
    total_dim = (matrix_size + 2 * border) * scale
    f_color = finder_color or dark_color

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_dim} {total_dim}" width="{total_dim}" height="{total_dim}">',
        f'<rect width="100%" height="100%" fill="{light_color}"/>',
    ]

    for r in range(matrix_size):
        for c in range(matrix_size):
            if not matrix[r][c]:
                continue
            x = (c + border) * scale
            y = (r + border) * scale

            if is_finder_module(r, c, matrix_size):
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{scale}" height="{scale}" fill="{f_color}"/>'
                )
            else:
                if shape == "dot":
                    cx = x + scale / 2.0
                    cy = y + scale / 2.0
                    radius = scale * 0.42
                    svg_parts.append(
                        f'<circle cx="{cx}" cy="{cy}" r="{radius:.2f}" fill="{dark_color}"/>'
                    )
                elif shape == "rounded":
                    rx = max(2, int(scale * 0.35))
                    svg_parts.append(
                        f'<rect x="{x}" y="{y}" width="{scale}" height="{scale}" rx="{rx}" ry="{rx}" fill="{dark_color}"/>'
                    )
                else:
                    svg_parts.append(
                        f'<rect x="{x}" y="{y}" width="{scale}" height="{scale}" fill="{dark_color}"/>'
                    )

    if logo_icon or logo_image_path:
        logo_size = int(total_dim * 0.22)
        cx = total_dim // 2
        cy = total_dim // 2
        logo_x = cx - logo_size // 2
        logo_y = cy - logo_size // 2
        pad = max(4, int(scale * 0.5))
        back_rx = int(logo_size * 0.25)

        svg_parts.append(
            f'<rect x="{logo_x - pad}" y="{logo_y - pad}" '
            f'width="{logo_size + 2 * pad}" height="{logo_size + 2 * pad}" '
            f'rx="{back_rx}" ry="{back_rx}" fill="{light_color}"/>'
        )

        # Render logo/icon as high-res PNG base64 data URI inside SVG image tag
        icon_png_bytes: bytes | None = None
        if logo_image_path and Path(logo_image_path).is_file():
            try:
                custom_img = Image.open(logo_image_path).convert("RGBA")
                custom_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
                b = io.BytesIO()
                custom_img.save(b, format="PNG")
                icon_png_bytes = b.getvalue()
            except (OSError, ValueError):
                pass
        elif logo_icon:
            icon_img = create_preset_icon_image(logo_icon, logo_size, color=f_color)
            b = io.BytesIO()
            icon_img.save(b, format="PNG")
            icon_png_bytes = b.getvalue()

        if icon_png_bytes:
            b64_str = base64.b64encode(icon_png_bytes).decode("ascii")
            svg_parts.append(
                f'<image href="data:image/png;base64,{b64_str}" '
                f'x="{logo_x}" y="{logo_y}" width="{logo_size}" height="{logo_size}"/>'
            )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def save_qr_code(
    data: str,
    target_path: Path,
    error_level: str = "m",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
    scale: int = 10,
    border: int = 4,
    shape: ShapeType = "square",
    finder_color: str | None = None,
    logo_icon: str | None = None,
    logo_image_path: Path | str | None = None,
) -> None:
    """Save QR code directly to target file path (PNG or SVG) with artistic options."""
    kind = target_path.suffix.lstrip(".").lower()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if kind == "svg":
        svg_content = generate_qr_svg(
            data=data,
            error_level=error_level,
            dark_color=dark_color,
            light_color=light_color,
            scale=scale,
            border=border,
            shape=shape,
            finder_color=finder_color,
            logo_icon=logo_icon,
            logo_image_path=logo_image_path,
        )
        target_path.write_text(svg_content, encoding="utf-8")
    else:
        png_data = generate_qr_png_bytes(
            data=data,
            error_level=error_level,
            dark_color=dark_color,
            light_color=light_color,
            scale=scale,
            border=border,
            shape=shape,
            finder_color=finder_color,
            logo_icon=logo_icon,
            logo_image_path=logo_image_path,
        )
        target_path.write_bytes(png_data)
