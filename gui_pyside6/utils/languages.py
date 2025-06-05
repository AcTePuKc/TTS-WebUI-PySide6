from __future__ import annotations

import json
from pathlib import Path


_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"
_USER_LANG_DIR = Path.home() / ".hybrid_tts" / "translations"


def _load_language_meta(directory: Path) -> dict[str, str]:
    languages: dict[str, str] = {}
    lang_file = directory / "languages.json"
    if lang_file.exists():
        try:
            with lang_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                languages.update({str(k): str(v) for k, v in data.items()})
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        code = item.get("code")
                        name = item.get("name") or item.get("language")
                        if code and name:
                            languages[str(code)] = str(name)
        except Exception:
            pass
    else:
        for meta in directory.glob("*.json"):
            if meta.name == "languages.json":
                continue
            try:
                with meta.open("r", encoding="utf-8") as f:
                    info = json.load(f)
                code = info.get("code") or meta.stem
                name = info.get("language") or info.get("name")
                if code and name:
                    languages[str(code)] = str(name)
            except Exception:
                continue
    return languages


def get_available_languages() -> dict[str, str]:
    """Return mapping of language code to display name."""
    languages: dict[str, str] = {}
    languages.update(_load_language_meta(_RESOURCES_DIR))
    if _USER_LANG_DIR.exists():
        languages.update({k: v for k, v in _load_language_meta(_USER_LANG_DIR).items() if k not in languages})
    if not languages:
        languages = {"en": "English"}
    return languages


def find_qm_file(code: str) -> Path | None:
    """Return path to compiled translation file for code if available."""
    for base in (_USER_LANG_DIR, _RESOURCES_DIR):
        qm = base / f"{code}.qm"
        if qm.exists():
            return qm
    return None
