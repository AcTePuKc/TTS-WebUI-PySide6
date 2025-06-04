from __future__ import annotations

import functools
import importlib
import importlib.util
import json
from pathlib import Path

from ..utils.install_utils import install_package_in_venv

def _call_backend(module: str, func: str, *args, **kwargs):
    """Import the given backend module on demand and run the requested function."""
    mod = importlib.import_module(f".{module}", __name__)
    return getattr(mod, func)(*args, **kwargs)


BACKENDS = {
    "pyttsx3": functools.partial(_call_backend, "pyttsx_backend", "synthesize_to_file"),
    "gtts": functools.partial(_call_backend, "gtts_backend", "synthesize_to_file"),
    "bark": functools.partial(_call_backend, "bark_backend", "synthesize_to_file"),
    "tortoise": functools.partial(_call_backend, "tortoise_backend", "synthesize_to_file"),
    "edge_tts": functools.partial(_call_backend, "edge_tts_backend", "synthesize_to_file"),
    "demucs": functools.partial(_call_backend, "demucs_backend", "separate_audio"),
    "mms": functools.partial(_call_backend, "mms_backend", "synthesize_to_file"),
}

def get_edge_voices(locale: str | None = None) -> list[str]:
    """Return list of available Edge TTS voices."""
    try:
        return _call_backend("edge_tts_backend", "list_voices", locale=locale)
    except Exception:
        return []

TRANSCRIBERS = {
    "whisper": functools.partial(_call_backend, "whisper_backend", "transcribe_to_text"),
}

def available_transcribers():
    return list(TRANSCRIBERS.keys())

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


def get_mms_languages() -> list[tuple[str, str]]:
    """Return list of available MMS languages."""
    try:
        from .mms_backend import get_mms_languages as _get
        return _get()
    except Exception:
        return [("English", "eng")]

def missing_backend_packages(name: str) -> list[str]:
    return [pkg for pkg in _get_backend_packages(name) if importlib.util.find_spec(pkg) is None]

def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)

def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        install_package_in_venv(missing)
