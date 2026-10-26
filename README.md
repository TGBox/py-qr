# py-qr

A python app to generate and read QR-codes.

## Voraussetzungen

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Qt 6 (wird automatisch über uv installiert)

## Setup & Ausführung

```bash
uv sync

# GUI starten
uv run main
# oder:
uv run py-qr

# Tests ausführen
uv run test

# Standalone-Exe mit PyInstaller bauen
uv run build
```

## Framework

Dieses Projekt verwendet **PySide6**.

## Projektstruktur

```
py-qr/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── build.py
│   └── tools.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md
```