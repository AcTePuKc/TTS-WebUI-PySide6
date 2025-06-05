from __future__ import annotations

import functools
import importlib
import importlib.util
import json
import sys
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
    "vocos": functools.partial(_call_backend, "vocos_backend", "reconstruct_audio"),
    "kokoro": functools.partial(_call_backend, "kokoro_backend", "synthesize_to_file"),
    "chatterbox": functools.partial(_call_backend, "chatterbox_backend", "synthesize_to_file"),
}

def get_edge_voices(locale: str | None = None) -> list[str]:
    """Return list of available Edge TTS voices."""
    if "edge_tts" not in sys.modules:
        try:
            found = importlib.util.find_spec("edge_tts") is not None
        except Exception:
            found = False
        if not found:
            ensure_backend_installed("edge_tts")
    return _call_backend("edge_tts_backend", "list_voices", locale=locale)


def get_kokoro_voices() -> list[tuple[str, str]]:
    """Return display names and identifiers for Kokoro voices."""
    try:
        return _call_backend("kokoro_backend", "list_voices")
    except Exception:
        return []


def get_chatterbox_voices() -> list[tuple[str, str]]:
    """Return available Chatterbox voice names and file paths."""
    try:
        return _call_backend("chatterbox_backend", "list_voices")
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


def _get_module_name(package_spec: str) -> str:
    """Return the importable module name for the given requirement spec."""
    try:
        from packaging.requirements import Requirement

        req = Requirement(package_spec)
        name = req.name
    except Exception:
        # Fallback to a simple split if packaging is not available or parsing fails
        name = package_spec.split("@")[0].strip().split()[0]

    # Normalize to a valid module name (pip packages may use dashes or casing)
    return name.replace("-", "_").lower()


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
    missing = []
    for pkg in _get_backend_packages(name):
        module_name = _get_module_name(pkg)
        if importlib.util.find_spec(module_name) is None:
            missing.append(pkg)
    return missing

def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)

def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        install_package_in_venv(missing)
