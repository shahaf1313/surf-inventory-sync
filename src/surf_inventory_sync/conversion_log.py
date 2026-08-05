"""Keeps a running history of every conversion (one row per successful
export) in a CSV file next to config.json, so the "History" tab can plot
exchange rate over time. Plain CSV rather than a database: the volume is
tiny (a few conversions per year) and it stays human-readable/inspectable
if dad ever wants to peek at it directly."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

_FIELDNAMES = ["timestamp", "source_file", "exchange_rate", "start_item_number", "item_count"]


def _default_log_path() -> Path:
    import os

    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "surf-inventory-sync" / "conversions_log.csv"


@dataclass(frozen=True)
class ConversionLogEntry:
    timestamp: datetime
    source_file: str
    exchange_rate: float
    start_item_number: int
    item_count: int

    def to_csv_row(self) -> dict:
        row = asdict(self)
        row["timestamp"] = self.timestamp.isoformat(timespec="seconds")
        return row

    @staticmethod
    def from_csv_row(row: dict) -> "ConversionLogEntry":
        return ConversionLogEntry(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source_file=row["source_file"],
            exchange_rate=float(row["exchange_rate"]),
            start_item_number=int(row["start_item_number"]),
            item_count=int(row["item_count"]),
        )


def append_log_entry(entry: ConversionLogEntry, path: Path | None = None) -> None:
    path = path or _default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        if is_new_file:
            writer.writeheader()
        writer.writerow(entry.to_csv_row())


def load_log_entries(path: Path | None = None) -> list[ConversionLogEntry]:
    path = path or _default_log_path()
    if not path.exists():
        return []
    entries = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                entries.append(ConversionLogEntry.from_csv_row(row))
            except (KeyError, ValueError):
                continue  # skip a corrupt/partial row rather than fail the whole read
    entries.sort(key=lambda e: e.timestamp)
    return entries
