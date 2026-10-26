"""PyInstaller build script to create standalone single-file executable for py-qr."""

import sys

import PyInstaller.__main__


def main() -> None:
    args = (
        sys.argv[1:]
        if len(sys.argv) > 1
        else [
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--collect-all",
            "zxingcpp",
            "--collect-all",
            "segno",
            "--name",
            "py-qr",
            "src/main.py",
        ]
    )
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
