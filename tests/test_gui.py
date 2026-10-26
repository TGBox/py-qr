from src.core.generator import save_qr_code
from src.core.history import HistoryManager
from src.core.parser import EmailConfig, PayloadType, VCardConfig, WifiConfig
from src.gui.main_window import MainWindow
from src.gui.tabs.generator_tab import GeneratorTab
from src.gui.tabs.history_tab import HistoryTab
from src.gui.tabs.reader_tab import ReaderTab


def test_main_window_init(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    window = MainWindow(history_manager=manager)
    qtbot.addWidget(window)

    assert "py-qr" in window.windowTitle()
    assert window.tabs is not None
    assert window.tabs.count() == 3
    assert window.menuBar() is not None


def test_main_window_fullscreen_toggle(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    window = MainWindow(history_manager=manager)
    qtbot.addWidget(window)

    assert not window.isFullScreen()

    window.toggle_fullscreen()
    assert window.isFullScreen()

    window.toggle_fullscreen()
    assert not window.isFullScreen()


def test_main_window_theme_toggle(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    window = MainWindow(history_manager=manager)
    qtbot.addWidget(window)

    initial_theme = window.settings.value("theme")
    window.toggle_theme()
    new_theme = window.settings.value("theme")
    assert new_theme != initial_theme


def test_generator_tab_modes_and_wifi(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    tab = GeneratorTab(history_manager=manager)
    qtbot.addWidget(tab)

    # Initial text mode
    payload, ptype, _ = tab.get_current_payload()
    assert ptype in ("url", "text")
    assert "github.com" in payload

    # Switch to WiFi
    tab.radio_wifi.setChecked(True)
    assert tab.input_stack.currentIndex() == 1
    assert tab.combo_error.currentData() == "h"

    # Pre-populate WiFi data
    config = WifiConfig(ssid="OfficeGuest", password="SecretWifiPassword", security="WPA")
    tab.load_wifi_data(config)
    payload, ptype, title = tab.get_current_payload()
    assert ptype == "wifi"
    assert "OfficeGuest" in title
    assert "WIFI:T:WPA;S:OfficeGuest;P:SecretWifiPassword;" in payload


def test_reader_tab_decoding(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    tab = ReaderTab(history_manager=manager)
    qtbot.addWidget(tab)

    # Generate a test QR image file
    qr_file = tmp_path / "sample_qr.png"
    save_qr_code("https://example.com/test", qr_file)

    tab.decode_from_path(qr_file)

    # Wait for active worker to complete
    qtbot.waitUntil(lambda: tab.last_result is not None, timeout=3000)

    assert tab.last_result.payload_type == PayloadType.URL
    assert tab.last_result.raw_text == "https://example.com/test"
    assert tab.result_stack.currentIndex() == 1  # URL result page

    # Check history was recorded
    items = manager.get_items()
    assert len(items) == 1
    assert items[0].action == "scan"
    assert items[0].raw_text == "https://example.com/test"


def test_history_tab_display_and_clear(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    manager.add_item("generate", "url", "https://example.com", "https://example.com")
    manager.add_item("scan", "wifi", "WLAN Guest", "WIFI:S:Guest;;")

    tab = HistoryTab(history_manager=manager)
    qtbot.addWidget(tab)

    assert tab.list_widget.count() == 2
    assert "WLAN Guest" in tab.list_widget.item(0).text()

    # Select first item and check details
    tab.list_widget.setCurrentRow(0)
    assert "WIFI:S:Guest;;" in tab.detail_text.toPlainText()
    assert tab.btn_copy_detail.isEnabled()

    # Clear via manager and refresh
    manager.clear_history()
    tab.refresh_history()
    assert tab.list_widget.count() == 1
    assert "Keine Einträge" in tab.list_widget.item(0).text()
    assert not tab.btn_copy_detail.isEnabled()


def test_light_and_dark_theme_palettes(qtbot, tmp_path):
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QApplication

    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    window = MainWindow(history_manager=manager)
    qtbot.addWidget(window)
    app = QApplication.instance()

    # Apply Light Theme
    window.set_theme("light")
    palette = app.palette()
    assert palette.color(QPalette.ColorRole.Window).name() == "#f8fafc"
    assert palette.color(QPalette.ColorRole.Base).name() == "#ffffff"
    assert palette.color(QPalette.ColorRole.Text).name() == "#0f172a"
    # Ensure generator tab color button has icon and no hardcoded dark inline background
    assert not window.generator_tab.btn_dark_color.icon().isNull()
    assert "background-color" not in window.generator_tab.btn_dark_color.styleSheet()

    # Apply Dark Theme
    window.set_theme("dark")
    palette = app.palette()
    assert palette.color(QPalette.ColorRole.Window).name() == "#0f172a"
    assert palette.color(QPalette.ColorRole.Base).name() == "#1e293b"
    assert palette.color(QPalette.ColorRole.Text).name() == "#f8fafc"


def test_generator_tab_vcard_and_email(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    tab = GeneratorTab(history_manager=manager)
    qtbot.addWidget(tab)

    # vCard mode
    tab.radio_vcard.setChecked(True)
    assert tab.input_stack.currentIndex() == 2
    vc = VCardConfig(first_name="Max", last_name="Muster", phone="012345", email="m@m.de")
    tab.load_vcard_data(vc)
    payload, ptype, title = tab.get_current_payload()
    assert ptype == "vcard"
    assert "BEGIN:VCARD" in payload
    assert "Max Muster" in title

    # Email mode
    tab.radio_email.setChecked(True)
    assert tab.input_stack.currentIndex() == 3
    em = EmailConfig(to="kontakt@firma.de", subject="Projekt Test", body="Hallo Welt")
    tab.load_email_data(em)
    payload, ptype, title = tab.get_current_payload()
    assert ptype == "email"
    assert "mailto:kontakt@firma.de" in payload
    assert "kontakt@firma.de" in title


def test_reader_tab_vcard_and_email_decoding(qtbot, tmp_path):
    from src.core.parser import format_email_payload, format_vcard_payload

    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    tab = ReaderTab(history_manager=manager)
    qtbot.addWidget(tab)

    # Decode vCard
    vc = VCardConfig(first_name="Anna", last_name="Schmidt", phone="+49111", email="anna@test.de")
    vcard_qr = tmp_path / "vcard.png"
    save_qr_code(format_vcard_payload(vc), vcard_qr)
    tab.decode_from_path(vcard_qr)
    qtbot.waitUntil(lambda: tab.last_result is not None, timeout=3000)
    assert tab.last_result.payload_type == PayloadType.VCARD
    assert tab.result_stack.currentIndex() == 4
    assert "Anna Schmidt" in tab.vcard_details_label.text()

    # Decode Email
    em = EmailConfig(to="support@py-qr.org", subject="Hilfe", body="Frage")
    email_qr = tmp_path / "email.png"
    save_qr_code(format_email_payload(em), email_qr)
    tab.decode_from_path(email_qr)
    qtbot.waitUntil(
        lambda: tab.last_result is not None and tab.last_result.payload_type == PayloadType.EMAIL,
        timeout=3000,
    )
    assert tab.result_stack.currentIndex() == 5
    assert "support@py-qr.org" in tab.email_details_label.text()


def test_card_dialog_instantiation_and_preview(qtbot):
    from src.gui.dialogs.card_dialog import CardDialog

    dialog = CardDialog(
        qr_data="WIFI:S:MyGuestNet;P:Secret99;;",
        payload_type="wifi",
    )
    qtbot.addWidget(dialog)
    dialog._update_preview()
    assert "Gäste-WLAN" in dialog.input_title.text()
    assert dialog.combo_size.currentData() == "A6"
    assert dialog.preview_label.pixmap() is not None


def test_history_tab_search_and_filter(qtbot, tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=history_file)
    manager.add_item("generate", "url", "GitHub", "https://github.com")
    manager.add_item("scan", "wifi", "WLAN Gast", "WIFI:S:Gast;;")
    manager.add_item("generate", "email", "Support Mail", "mailto:help@py-qr.org")

    tab = HistoryTab(history_manager=manager)
    qtbot.addWidget(tab)

    assert tab.list_widget.count() == 3

    # Filter by text search
    tab.search_input.setText("GitHub")
    assert tab.list_widget.count() == 1
    assert "GitHub" in tab.list_widget.item(0).text()

    # Clear search
    tab.search_input.setText("")
    assert tab.list_widget.count() == 3

    # Filter by type "wifi"
    idx = tab.type_filter.findData("wifi")
    tab.type_filter.setCurrentIndex(idx)
    assert tab.list_widget.count() == 1
    assert "WLAN Gast" in tab.list_widget.item(0).text()

    # Reset filter
    idx_all = tab.type_filter.findData("all")
    tab.type_filter.setCurrentIndex(idx_all)
    assert tab.list_widget.count() == 3
