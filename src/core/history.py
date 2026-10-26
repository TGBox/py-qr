"""Local history manager for scanned and generated QR codes."""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class HistoryItem:
    """A single scanned or generated QR code history record."""

    id: str
    timestamp: str
    action: str  # "scan" or "generate"
    payload_type: str  # "text", "url", "wifi"
    title: str
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def get_default_history_path() -> Path:
    """Return default path to history.json in AppData on Windows or ~/.py-qr elsewhere."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = Path(appdata) / "py-qr"
    else:
        base_dir = Path.home() / ".py-qr"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "history.json"


class HistoryManager:
    """Manages persistent history storage."""

    def __init__(self, storage_path: Path | None = None, max_items: int = 20):
        self.storage_path = storage_path or get_default_history_path()
        self.max_items = max_items
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_records([])

    def _read_records(self) -> list[dict[str, Any]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_records(self, records: list[dict[str, Any]]) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get_items(self) -> list[HistoryItem]:
        """Return all history items, newest first."""
        records = self._read_records()
        items = []
        for r in records:
            items.append(
                HistoryItem(
                    id=r.get("id", ""),
                    timestamp=r.get("timestamp", ""),
                    action=r.get("action", "scan"),
                    payload_type=r.get("payload_type", "text"),
                    title=r.get("title", ""),
                    raw_text=r.get("raw_text", ""),
                    metadata=r.get("metadata", {}),
                )
            )
        return items

    def add_item(
        self,
        action: str,
        payload_type: str,
        title: str,
        raw_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> HistoryItem:
        """Add a new item to history and prune if exceeding max_items."""
        item = HistoryItem(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action=action,
            payload_type=payload_type,
            title=title,
            raw_text=raw_text,
            metadata=metadata or {},
        )

        records = self._read_records()
        # Insert at the beginning (newest first)
        records.insert(0, asdict(item))

        # Enforce max items
        if len(records) > self.max_items:
            records = records[: self.max_items]

        self._write_records(records)
        return item

    def clear_history(self) -> None:
        """Remove all history records."""
        self._write_records([])

    def delete_item(self, item_id: str) -> bool:
        """Delete a single item by id."""
        records = self._read_records()
        new_records = [r for r in records if r.get("id") != item_id]
        if len(new_records) != len(records):
            self._write_records(new_records)
            return True
        return False
