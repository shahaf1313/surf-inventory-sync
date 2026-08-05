import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.config import Settings, load_settings, save_settings  # noqa: E402


def test_load_settings_returns_defaults_when_no_file(tmp_path):
    settings = load_settings(tmp_path / "does_not_exist.json")
    assert settings == Settings()


def test_save_then_load_roundtrips(tmp_path):
    path = tmp_path / "subdir" / "config.json"
    save_settings(Settings(exchange_rate=3.85, next_item_number=8886), path)

    loaded = load_settings(path)
    assert loaded.exchange_rate == 3.85
    assert loaded.next_item_number == 8886


def test_load_settings_tolerates_corrupt_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not valid json{{{", encoding="utf-8")
    assert load_settings(path) == Settings()
