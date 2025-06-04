from __future__ import annotations

import functools
import importlib
import importlib.util
import json
from pathlib import Path

from ..utils.install_utils import install_package_in_venv

def _call_backend(module: str, *args, **kwargs):
    """Import the given backend module on demand and run it."""
    mod = importlib.import_module(f".{module}", __name__)
    return mod.synthesize_to_file(*args, **kwargs)

BACKENDS = {
    "pyttsx3": functools.partial(_call_backend, "pyttsx_backend"),
    "gtts": functools.partial(_call_backend, "gtts_backend"),
}

def available_backends():
    return list(BACKENDS.keys())

_REQ_FILE = Path(__file__).with_name("backend_requirements.json")

def _get_backend_packages(name: str) -> list[str]:
    if not _REQ_FILE.exists():
        return []
    with _REQ_FILE.open() as f:
        reqs: dict[str, list[str]] = json.load(f)
    return reqs.get(name, [])

def get_gtts_languages():
    try:
        from gtts import lang
        return lang.tts_langs()
    except Exception:
        return {"en": "English"}

def missing_backend_packages(name: str) -> list[str]:
    return [pkg for pkg in _get_backend_packages(name) if importlib.util.find_spec(pkg) is None]

def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)

def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        install_package_in_venv(missing)
