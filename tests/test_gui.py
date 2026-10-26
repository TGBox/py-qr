from src.core.generator import save_qr_code
from src.core.history import HistoryManager
from src.core.parser import PayloadType, WifiConfig
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
