"""Entry point for the py-qr desktop application."""

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("py-qr")
    app.setOrganizationName("TGBox")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
