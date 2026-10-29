"""Settings and log locations (%LOCALAPPDATA%\\EasyChange on Windows)."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

DEFAULT_HOTKEY = "alt+8"


def app_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share"
    d = Path(base) / "EasyChange"
    d.mkdir(parents=True, exist_ok=True)
    return d


def path() -> Path:
    return app_dir() / "config.json"


def pid_file() -> Path:
    return app_dir() / "hotkey.pid"


def load() -> dict:
    p = path()
    if not p.exists():
        p.write_text(json.dumps({"hotkey": DEFAULT_HOTKEY}, indent=2))
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def setup_logging() -> None:
    logging.basicConfig(filename=app_dir() / "easychange.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
