"""Persists the last-used exchange rate and starting item number between
runs, purely as a convenience default the user can overwrite - both fields
stay manually editable in the UI every time, per the user's workflow."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


def _default_config_path() -> Path:
    # %APPDATA% on Windows, ~/.config elsewhere.
    import os

    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "surf-inventory-sync" / "config.json"


@dataclass
class Settings:
    exchange_rate: float = 4.1
    next_item_number: int = 1


def load_settings(path: Path | None = None) -> Settings:
    path = path or _default_config_path()
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Settings(
            exchange_rate=float(data.get("exchange_rate", Settings.exchange_rate)),
            next_item_number=int(data.get("next_item_number", Settings.next_item_number)),
        )
    except (json.JSONDecodeError, ValueError, TypeError):
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = path or _default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
