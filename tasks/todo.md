# Task List: py-qr

## Phase 1: Environment & Core Engine (TDD)

### Task 1: Dependencies Setup & Verification [x]

- **Description:** Add `segno`, `zxing-cpp`, `pillow`, and `pytest-qt` to `pyproject.toml` via `uv add` and verify that imports succeed.
- **Acceptance criteria:**
  - [x] `pyproject.toml` contains `segno`, `zxing-cpp`, `pillow` under dependencies, and `pytest-qt` under dev dependencies.
  - [x] `python -c "import segno, zxingcpp, PIL"` runs with exit code 0.
- **Verification:**
  - `uv sync`
  - `uv run python -c "import segno, zxingcpp, PIL; print('Imports OK')"`
- **Dependencies:** None
- **Files touched:** `pyproject.toml`, `uv.lock`
- **Scope:** S (2 files)

### Task 2: Core Payload Parser (`src/core/parser.py`) [x]

- **Description:** Implement smart payload parsing and formatting for QR codes. Detect and parse WiFi config strings (`WIFI:S:...;T:...;P:...;H:...;;`), URLs (`http://`, `https://`), and plain text.
- **Acceptance criteria:**
  - [x] `parse_payload(text: str) -> ScanResult` correctly identifies `PayloadType.WIFI`, `PayloadType.URL`, and `PayloadType.TEXT`.
  - [x] Structured fields for WiFi (SSID, password, auth type, hidden) are extracted cleanly.
  - [x] Generates standard WiFi QR string format from parameters.
  - [x] Comprehensive unit tests in `tests/test_parser.py` cover all valid formats, edge cases, and malformed strings.
- **Verification:**
  - `uv run pytest tests/test_parser.py`
- **Dependencies:** Task 1
- **Files touched:** `src/core/parser.py`, `tests/test_parser.py`
- **Scope:** S (2 files)

### Task 3: Core QR Generator (`src/core/generator.py`) [x]

- **Description:** Implement QR generation using `segno`. Support text and WiFi generation, customizable error correction levels (L, M, Q, H), customizable colors (dark/light), and output to PNG (bytes, file) and SVG (string, file).
- **Acceptance criteria:**
  - [x] `generate_qr_png_bytes(data: str, error_level: str, dark_color: str, light_color: str, scale: int) -> bytes` produces valid PNG bytes.
  - [x] `generate_qr_svg(data: str, error_level: str, dark_color: str, light_color: str) -> str` produces valid SVG markup.
  - [x] Unit tests in `tests/test_generator.py` verify generation, error correction levels, and color parameters.
- **Verification:**
  - `uv run pytest tests/test_generator.py`
- **Dependencies:** Task 1
- **Files touched:** `src/core/generator.py`, `tests/test_generator.py`
- **Scope:** S (2 files)

### Task 4: Core QR Reader (`src/core/reader.py`) [x]

- **Description:** Implement QR code reading using `zxing-cpp` and `Pillow`. Decode from file paths, raw image bytes, or PIL Image objects.
- **Acceptance criteria:**
  - [x] `decode_image(source: Path | bytes | Image.Image) -> Optional[ScanResult]` correctly decodes QR codes.
  - [x] Handles corrupt, empty, or non-QR images gracefully by returning `None` without unhandled exceptions.
  - [x] Unit tests in `tests/test_reader.py` test round-trip (generate QR with `generator.py` then decode with `reader.py`).
- **Verification:**
  - `uv run pytest tests/test_reader.py`
- **Dependencies:** Tasks 2, 3
- **Files touched:** `src/core/reader.py`, `tests/test_reader.py`
- **Scope:** S (2 files)

### Task 5: Core Local History (`src/core/history.py`) [x]

- **Description:** Implement persistent local history stored in user's AppData directory (`%APPDATA%/py-qr/history.json`).
- **Acceptance criteria:**
  - [x] Supports adding scan/generation events with timestamp, payload type, preview text, and full content.
  - [x] Keeps at most 20 recent items (pruning oldest).
  - [x] Provides a `clear_history()` method.
  - [x] Unit tests in `tests/test_history.py` test persistence, item limits, and clearing (using a temporary test file).
- **Verification:**
  - `uv run pytest tests/test_history.py`
- **Dependencies:** Task 2
- **Files touched:** `src/core/history.py`, `tests/test_history.py`
- **Scope:** S (2 files)

---

### Checkpoint: Foundation & Core Engine [x]

- [x] All unit tests pass: `uv run pytest`
- [x] Linting and formatting pass: `uv run ruff check .`

---

## Phase 2: GUI Shell & Theming

### Task 6: Modern Theme System (`src/gui/theme.py`) [x]

- **Description:** Implement Dark and Light themes with high contrast, modern design tokens, and Windows system theme auto-detection.
- **Acceptance criteria:**
  - [x] High quality Dark QSS and Light QSS with styled tabs, buttons, inputs, labels, and scrollbars.
  - [x] `detect_system_theme() -> str` detects Windows Dark/Light mode.
  - [x] `apply_theme(app: QApplication, theme_name: str)` applies stylesheets cleanly.
- **Verification:**
  - `uv run python -c "from src.gui.theme import detect_system_theme; print('System theme:', detect_system_theme())"`
- **Dependencies:** Task 1
- **Files touched:** `src/gui/theme.py`
- **Scope:** S (1 file)

### Task 7: Async Thread Workers (`src/gui/workers.py`) [x]

- **Description:** Implement background worker threads using `QThread` and Qt signals for decoding images and generating QR previews to keep the UI at 60 FPS.
- **Acceptance criteria:**
  - [x] `DecodeWorker` accepts image data/path and emits `finished(ScanResult)` or `failed(str)`.
  - [x] `GenerateWorker` accepts parameters and emits `finished(QPixmap)` or `failed(str)`.
  - [x] Non-blocking execution verified with unit test.
- **Verification:**
  - `uv run pytest tests/test_workers.py`
- **Dependencies:** Tasks 3, 4
- **Files touched:** `src/gui/workers.py`, `tests/test_workers.py`
- **Scope:** S (2 files)

### Task 8: Main Window Shell & Persistent Settings (`src/gui/main_window.py`) [x]

- **Description:** Build the `MainWindow` with menu bar, tab widget, theme toggle, fullscreen toggle (`F11`), and geometry persistence with `QSettings`.
- **Acceptance criteria:**
  - [x] Window restores previous size, position, and active theme on launch.
  - [x] `F11` toggles between windowed and fullscreen seamlessly.
  - [x] UI labels and menus in German ("Datei", "Ansicht", "Hilfe", "Vollbild umschalten", "Theme wechseln").
- **Verification:**
  - `uv run pytest tests/test_gui.py -k test_main_window`
- **Dependencies:** Tasks 6, 7
- **Files touched:** `src/gui/main_window.py`, `tests/test_gui.py`
- **Scope:** M (2 files)

---

### Checkpoint: Window & Shell Verification [x]

- [x] Main window launches cleanly: `uv run py-qr`
- [x] F11 toggles fullscreen

---

## Phase 3: Tabs & User Workflows

### Task 9: Generator Tab (`src/gui/tabs/generator_tab.py`) [x]

- **Description:** Implement the "Generieren" tab with live preview, text and WiFi input modes, color pickers, error correction selector, and export options.
- **Acceptance criteria:**
  - [x] Mode switch between "Freitext / URL" and "WLAN".
  - [x] For WiFi: SSID, password, security dropdown (WPA/WPA2/WPA3, WEP, Offen), hidden checkbox; auto-selects 'H' error correction.
  - [x] Live preview updates on typing with debouncing (150ms).
  - [x] Export buttons: "Als PNG speichern", "Als SVG speichern", "In Zwischenablage kopieren".
  - [x] Successful generation is recorded in local history.
- **Verification:**
  - `uv run pytest tests/test_gui.py -k test_generator_tab`
- **Dependencies:** Tasks 3, 5, 7, 8
- **Files touched:** `src/gui/tabs/generator_tab.py`, `src/gui/main_window.py`, `tests/test_gui.py`
- **Scope:** M (3 files)

### Task 10: Reader Tab (`src/gui/tabs/reader_tab.py`) [x]

- **Description:** Implement the "Lesen" tab with drag-and-drop zone, file open dialog, global `Strg+V` clipboard paste, and smart action buttons.
- **Acceptance criteria:**
  - [x] Dragging and dropping an image decodes and displays the QR code.
  - [x] Pressing `Strg+V` with an image in clipboard immediately decodes it.
  - [x] Decoded results show raw text + smart actions:
    - URL: "Im Browser öffnen", "Link kopieren".
    - WiFi: Formatted SSID, security, password, "Passwort kopieren", "In Generator übernehmen".
    - Plain text: "Text kopieren".
  - [x] Successful scan is recorded in local history.
- **Verification:**
  - `uv run pytest tests/test_gui.py -k test_reader_tab`
- **Dependencies:** Tasks 2, 4, 5, 7, 8
- **Files touched:** `src/gui/tabs/reader_tab.py`, `src/gui/main_window.py`, `tests/test_gui.py`
- **Scope:** M (3 files)

### Task 11: History Tab (`src/gui/tabs/history_tab.py`) [x]

- **Description:** Implement the "Verlauf" tab displaying recent scans and generations with quick actions and clear button.
- **Acceptance criteria:**
  - [x] Lists the last 20 entries with type badge (WLAN, URL, Text, Scan/Erstellt) and timestamp.
  - [x] Clicking an item shows details or allows copying/re-generating.
  - [x] "Verlauf leeren" button clears history after confirmation.
- **Verification:**
  - `uv run pytest tests/test_gui.py -k test_history_tab`
- **Dependencies:** Tasks 5, 8, 9, 10
- **Files touched:** `src/gui/tabs/history_tab.py`, `src/gui/main_window.py`, `tests/test_gui.py`
- **Scope:** M (3 files)

---

### Checkpoint: Full Functional Integration [x]

- [x] End-to-end user workflows tested: `uv run pytest`
- [x] Manual smoke test running `uv run main`

---

## Phase 4: Standalone Executable Build

### Task 12: PyInstaller Packaging Script (`src/build.py`) & Verification [x]

- **Description:** Update `src/build.py` to create a standalone, single-file Windows executable (`py-qr.exe`) and test the build process.
- **Acceptance criteria:**
  - [x] `src/build.py` runs PyInstaller with `--onefile --windowed --name py-qr`.
  - [x] Handles required data/binary dependencies for `zxing-cpp` and `segno`.
  - [x] `uv run build` finishes with exit code 0 and produces `dist/py-qr.exe`.
- **Verification:**
  - `uv run build`
  - Verify that `dist/py-qr.exe` exists and is executable.
- **Dependencies:** Tasks 8, 9, 10, 11
- **Files touched:** `src/build.py`
- **Scope:** S (1 file)

---

### Checkpoint: Final Release [x]

- [x] Executable builds cleanly and runs independently.
- [x] Code formatted with `uv run ruff format .` and passes `uv run ruff check .`.

---
