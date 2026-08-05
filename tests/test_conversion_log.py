import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.conversion_log import (  # noqa: E402
    ConversionLogEntry,
    append_log_entry,
    load_log_entries,
)


def test_load_returns_empty_list_when_no_file(tmp_path):
    assert load_log_entries(tmp_path / "missing.csv") == []


def test_append_then_load_roundtrips(tmp_path):
    path = tmp_path / "log.csv"
    entry = ConversionLogEntry(
        timestamp=datetime(2026, 8, 5, 14, 30, 0),
        source_file="Orderform_North_KB_SS26.xlsx",
        exchange_rate=3.7,
        start_item_number=8886,
        item_count=172,
    )
    append_log_entry(entry, path)

    loaded = load_log_entries(path)
    assert loaded == [entry]


def test_multiple_entries_are_appended_and_sorted_by_time(tmp_path):
    path = tmp_path / "log.csv"
    later = ConversionLogEntry(datetime(2026, 8, 5, 12, 0), "b.xlsx", 4.0, 9058, 548)
    earlier = ConversionLogEntry(datetime(2026, 1, 1, 9, 0), "a.xlsx", 3.7, 8886, 172)

    append_log_entry(later, path)
    append_log_entry(earlier, path)

    loaded = load_log_entries(path)
    assert [e.source_file for e in loaded] == ["a.xlsx", "b.xlsx"]


def test_corrupt_row_is_skipped_not_fatal(tmp_path):
    path = tmp_path / "log.csv"
    good = ConversionLogEntry(datetime(2026, 1, 1, 9, 0), "a.xlsx", 3.7, 8886, 172)
    append_log_entry(good, path)
    with path.open("a", encoding="utf-8") as f:
        f.write("not,a,valid,csv,row\n")

    loaded = load_log_entries(path)
    assert len(loaded) == 1
    assert loaded[0].source_file == "a.xlsx"
