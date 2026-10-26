# Spec: py-qr (Desktop QR Code Studio & Reader)

## Objective

A lightweight, high-performance desktop application built with Python 3.11+ and PySide6 to generate and decode QR codes offline.
Key goals:

- **Instant Decoding**: Decode QR codes from image files, drag & drop, and direct clipboard pastes (`Ctrl+V` / `Strg+V`) in under 1 second.
- **Smart Parsing**: Automatically detect payload type (URLs, WiFi configs, vCard, plain text) and present actionable controls (e.g. "Im Browser öffnen", "Passwort kopieren").
- **Reactive Generation**: Real-time QR preview as the user types, with support for free text and structured WiFi setup (SSID, Password, Security type).
- **Styling & Export**: Customizable foreground/background colors, selectable error correction levels (L, M, Q, H), export to PNG/SVG, and "Bild in Zwischenablage kopieren".
- **Local History**: Keep the last 20 generated/scanned items locally with a "Verlauf leeren" option.
- **Standalone Distribution**: Package smoothly into a portable single-file Windows executable via PyInstaller.

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager & Environment**: `uv`
- **GUI Framework**: `PySide6` (Qt 6.7+)
- **QR Code Encoding**: `segno` (Pure-Python, fast SVG/PNG generation, color support, no C-compiler needed)
- **QR Code Decoding**: `zxing-cpp` (Fast C++-based port, robust, easily bundles into PyInstaller) + `Pillow` (image loading and format conversion)
- **Settings & History**: `QSettings` (window geometry, active theme) + local JSON storage in user app data (`%APPDATA%/py-qr/history.json`)
- **Linting & Formatting**: `ruff`
- **Testing**: `pytest`, `pytest-qt`
- **Build / Packaging**: `pyinstaller`

## Commands

- **Install / Sync dependencies**: `uv sync`
- **Add core dependencies**: `uv add segno zxing-cpp pillow`
- **Add dev dependencies**: `uv add --dev pytest pytest-qt ruff pyinstaller`
- **Run Application**: `uv run py-qr` (or `uv run src/main.py`)
- **Run Tests**: `uv run pytest`
- **Run Linter**: `uv run ruff check .`
- **Run Formatter**: `uv run ruff format .`
- **Build Standalone Exe**: `uv run build`

## Project Structure

```text
py-qr/
├── src/
│   ├── __init__.py
│   ├── main.py              # Application entry point & Qt event loop
│   ├── build.py             # PyInstaller build automation script
│   ├── tools.py             # Formatting and linting helper scripts
│   ├── core/
│   │   ├── __init__.py
│   │   ├── generator.py     # QR generation logic (segno wrapper)
│   │   ├── reader.py        # QR decoding logic (zxing-cpp wrapper)
│   │   ├── parser.py        # Payload parsing (WiFi, URL, text detection)
│   │   └── history.py       # Recent scans & generations storage
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py   # Main window layout, tabs, menus, shortcuts (F11)
│       ├── tabs/
│       │   ├── __init__.py
│       │   ├── generator_tab.py  # Generation UI: text, wifi, color pickers, preview
│       │   ├── reader_tab.py     # Reader UI: dropzone, clipboard paste, smart actions
│       │   └── history_tab.py    # History list & action buttons
│       ├── theme.py         # Dark & Light stylesheets (QSS) and theme switching
│       └── workers.py       # QThread workers for non-blocking QR decode/render
├── tests/
│   ├── __init__.py
│   ├── test_generator.py    # Unit tests for QR generation & formats
│   ├── test_reader.py       # Unit tests for QR reading & decoding
│   ├── test_parser.py       # Unit tests for WiFi/URL parsing
│   ├── test_history.py      # Unit tests for history persistence
│   └── test_gui.py          # GUI tests using pytest-qt
├── docs/
│   ├── ideas/
│   │   └── py-qr-core.md
│   └── SPEC.md
├── pyproject.toml
└── README.md
```

## Code Style

- **Python Conventions**: PEP 8, typed functions (`def decode_image(image_path: Path) -> Optional[ScanResult]:`), full type annotations.
- **Language Rules**:
  - Code comments, docstrings, variable and function names in **English**.
  - User-facing UI strings (buttons, labels, dialogs, tooltips) in **German**.
- **PySide6 Guidelines**:
  - Keep business logic decoupled from Qt widgets (`src/core/` has zero UI dependency).
  - Use `QThread` and `Signal` for tasks taking >10ms (e.g. decoding large images).
  - Use `QSettings` for persisting window dimensions, position, and active theme.
  - Fullscreen support via `F11` (or menu item), switching smoothly between windowed and fullscreen.

### Code Example

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import zxingcpp
from PIL import Image


class PayloadType(Enum):
    URL = "url"
    WIFI = "wifi"
    TEXT = "text"


@dataclass
class ScanResult:
    """Represents the decoded QR code result."""

    raw_text: str
    payload_type: PayloadType
    metadata: dict[str, str]


def decode_qr(image_path: Path) -> Optional[ScanResult]:
    """Decode a QR code from a file without blocking UI."""
    with Image.open(image_path) as img:
        results = zxingcpp.read_barcodes(img)
        if not results:
            return None
        raw_text = results[0].text
        return parse_payload(raw_text)
```

## Testing Strategy

- **Framework**: `pytest` and `pytest-qt` (headless Qt tests with `qapp`).
- **Core Tests**:
  - `test_generator.py`: Verify PNG/SVG generation, error correction levels, color parameters.
  - `test_reader.py`: Test reading valid QR codes from synthetic PNG buffers, handling corrupt/unreadable images gracefully.
  - `test_parser.py`: Test WiFi format string parsing (`WIFI:S:MySSID;T:WPA;P:Secret;;`), URL detection (`https://...`), and fallback to raw text.
  - `test_history.py`: Verify adding, pruning (max 20 entries), and clearing history.
- **GUI Tests**:
  - Test tab switching, shortcut handling (`F11`, `Ctrl+V`), and clipboard interaction.
- **Packaging Smoke Test**:
  - Verify that running PyInstaller builds an `.exe` that starts and decodes a sample QR code without missing symbols or DLL errors.

## Boundaries

- **Always**:
  - Run `uv run pytest` and `uv run ruff check .` before declaring tasks complete.
  - Keep user-visible GUI strings in German.
  - Ensure windowed and fullscreen modes (F11) work seamlessly.
  - Handle invalid image files or empty clipboard gracefully without crashing.
- **Ask First**:
  - Adding heavy third-party dependencies beyond `segno`, `zxing-cpp`, `pillow`.
  - Introducing network/cloud features (offline-first is a strict promise).
- **Never**:
  - Run long-running or blocking file/decode operations on the Qt main GUI thread.
  - Store unencrypted sensitive WiFi passwords permanently without user knowledge (provide "Verlauf leeren").
  - Hardcode absolute file paths for assets or history files.

## Success Criteria

1. **Decode Performance**: Pasting a QR code image via `Strg+V` or drag-and-drop displays decoded content in < 500ms.
2. **Smart Actions**:
   - For WiFi QR codes, display SSID, security, and password with a single-click "Passwort kopieren" button.
   - For URL QR codes, provide an "Im Browser öffnen" button.
3. **Reactive Generation**: Typing text or WiFi credentials updates the QR code preview with debounce <= 150ms.
4. **Export Flexibility**: QR code can be saved as `.png`, `.svg`, or copied as an image directly to the system clipboard.
5. **Theme & Persistence**: Dark/Light theme toggle works instantly; window size and position are restored upon restart.
6. **Executable Build**: `uv run build` produces a standalone Windows `.exe` that runs independently on a clean Windows machine without Python installed.

## Open Questions

1. Should the initial theme follow the Windows system theme (Dark/Light mode detection) automatically on first launch?
2. Do you have a preferred default error correction level (Recommendation: `M` (15%) for regular text, `H` (30%) for WiFi or codes intended for printing)?
