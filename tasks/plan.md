# Implementation Plan: py-qr (Desktop QR Code Studio & Reader)

## Overview

A lightweight, fast, offline desktop application for Windows using Python 3.11+ and PySide6 to decode QR codes (files, drag & drop, clipboard paste) and generate customizable QR codes (live preview, text/WiFi, colors, SVG/PNG/clipboard export) with a persistent local history and single-file executable packaging.

## Architecture Decisions

1. **Decoupled Core Architecture**: All business logic (`src/core/`) is completely free of GUI dependencies, enabling 100% automated headless unit testing.
2. **Library Selection for Flawless PyInstaller Builds**:
   - `segno` for QR generation: pure Python, supports micro QR, structured WiFi, SVG, PNG, color customization, zero C-compiler required.
   - `zxing-cpp` + `Pillow` for QR reading: modern, extremely fast and robust C++ barcode engine with precompiled Windows wheels that cleanly package with PyInstaller (avoiding legacy `pyzbar` DLL loading issues).
3. **Responsive UI Threading**: All decoding and high-resolution rendering tasks execute in background `QThread` workers with Qt signal-slot communication.
4. **Theme & Settings Persistence**: Native `QSettings` saves window geometry, fullscreen state, and active theme. System theme (Windows Dark/Light mode) is detected automatically on first run.

## Task List

### Phase 1: Environment & Core Engine (TDD)

- [x] Task 1: Dependencies Setup & Verification
- [x] Task 2: Core Payload Parser (`src/core/parser.py`)
- [x] Task 3: Core QR Generator (`src/core/generator.py`)
- [x] Task 4: Core QR Reader (`src/core/reader.py`)
- [x] Task 5: Core Local History (`src/core/history.py`)

### Checkpoint: Core Engine Verification [x]

- [x] All unit tests pass (`uv run pytest`)
- [x] Code formatting and linting pass (`uv run ruff check .`)

### Phase 2: GUI Shell & Theming

- [x] Task 6: Modern Theme System with Windows Auto-Detection (`src/gui/theme.py`)
- [x] Task 7: Async Thread Workers (`src/gui/workers.py`)
- [x] Task 8: Main Window Shell & Persistent Settings (`src/gui/main_window.py`)

### Checkpoint: Window & Shell Verification [x]

- [x] Window opens cleanly in windowed mode and toggles fullscreen with F11
- [x] Theme toggles between Dark and Light mode seamlessly

### Phase 3: Tabs & User Workflows

- [x] Task 9: Generator Tab with Live Preview & WiFi Template (`src/gui/tabs/generator_tab.py`)
- [x] Task 10: Reader Tab with Dropzone, Clipboard (`Strg+V`) & Smart Actions (`src/gui/tabs/reader_tab.py`)
- [x] Task 11: History Tab with Quick Actions & Clear Option (`src/gui/tabs/history_tab.py`)

### Checkpoint: Full Functional Integration [x]

- [x] End-to-end QR generation (text & WiFi, colors, PNG/SVG/Clipboard) works
- [x] End-to-end QR decoding (file, drag-and-drop, clipboard paste) works
- [x] Full test suite passes (`uv run pytest`)

### Phase 4: Standalone Executable Build

- [x] Task 12: PyInstaller Packaging Script (`src/build.py`) & Build Verification

### Checkpoint: Final Release [x]

- [x] Single-file executable builds cleanly without warnings
- [x] Executable launches and functions independently

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| `zxing-cpp` missing runtime DLLs in PyInstaller | High | Tested early in Task 1 with quick standalone packaging smoke test |
| UI freezes during rapid typing in Generator | Med | Debounce timer (100ms) and background worker |
| Clipboard image format inconsistencies in Windows | Med | Support multiple image MIME types and QImage fallback |
| WiFi passwords exposed unintentionally | Low | Add warning label, quick "Verlauf leeren" button, and don't log empty attempts |
