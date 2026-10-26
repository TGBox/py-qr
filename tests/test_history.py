import tempfile
from pathlib import Path

from src.core.history import HistoryManager


def test_history_add_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_history.json"
        manager = HistoryManager(storage_path=file_path)

        assert len(manager.get_items()) == 0

        manager.add_item(
            action="scan",
            payload_type="url",
            title="https://github.com",
            raw_text="https://github.com",
        )

        items = manager.get_items()
        assert len(items) == 1
        assert items[0].title == "https://github.com"
        assert items[0].action == "scan"
        assert items[0].payload_type == "url"


def test_history_max_limit_pruning():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_history.json"
        manager = HistoryManager(storage_path=file_path, max_items=5)

        for i in range(10):
            manager.add_item(
                action="generate",
                payload_type="text",
                title=f"Item {i}",
                raw_text=f"Raw {i}",
            )

        items = manager.get_items()
        assert len(items) == 5
        # Most recent should be Item 9, oldest Item 5
        assert items[0].title == "Item 9"
        assert items[-1].title == "Item 5"


def test_history_clear():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_history.json"
        manager = HistoryManager(storage_path=file_path)

        manager.add_item(
            action="scan",
            payload_type="wifi",
            title="WLAN Home",
            raw_text="WIFI:S:Home;;",
        )
        assert len(manager.get_items()) == 1

        manager.clear_history()
        assert len(manager.get_items()) == 0
        assert file_path.exists()


def test_history_mask_password(tmp_path):
    file_path = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=file_path, mask_passwords=True)

    manager.add_item(
        action="scan",
        payload_type="wifi",
        title="WLAN SecretNet",
        raw_text="WIFI:T:WPA;S:SecretNet;P:TopSecretPassword;H:false;;",
        metadata={"ssid": "SecretNet", "password": "TopSecretPassword"},
    )

    items = manager.get_items()
    assert len(items) == 1
    assert "TopSecretPassword" not in items[0].raw_text
    assert "P:***;" in items[0].raw_text
    assert items[0].metadata.get("password") == "***"


def test_history_export_csv_and_json(tmp_path):
    file_path = tmp_path / "test_history.json"
    manager = HistoryManager(storage_path=file_path)

    manager.add_item("generate", "url", "https://example.com", "https://example.com")
    manager.add_item("scan", "text", "Notiz", "Mein geheimer Text")

    # CSV Export
    csv_file = tmp_path / "export.csv"
    manager.export_to_csv(csv_file)
    assert csv_file.exists()
    csv_text = csv_file.read_text(encoding="utf-8")
    assert "Zeitstempel" in csv_text
    assert "https://example.com" in csv_text
    assert "Mein geheimer Text" in csv_text

    # JSON Export
    json_file = tmp_path / "export.json"
    manager.export_to_json(json_file)
    assert json_file.exists()
    import json

    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert len(data) == 2
