from __future__ import annotations

import json
from pathlib import Path

PREF_FILE = Path.home() / ".hybrid_tts" / "preferences.json"


def load_preferences() -> dict:
    if PREF_FILE.exists():
        try:
            with PREF_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_preferences(prefs: dict) -> None:
    PREF_FILE.parent.mkdir(exist_ok=True)
    with PREF_FILE.open("w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)
