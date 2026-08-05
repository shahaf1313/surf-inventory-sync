#!/usr/bin/env python3
"""Entry point: launches the desktop app. On Windows, double-click this
file (or a shortcut to it) once Python + requirements.txt are installed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from surf_inventory_sync.gui import main  # noqa: E402

if __name__ == "__main__":
    main()
