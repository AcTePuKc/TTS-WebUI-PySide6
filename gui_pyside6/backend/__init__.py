from __future__ import annotations

import functools
import importlib
import importlib.util
from importlib import metadata
import json
import sys
from pathlib import Path

from datetime import datetime

from ..utils.install_utils import (
    install_package_in_venv,
    uninstall_package_from_venv,
)

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

# Explicit feature flags describing which optional parameters each backend
# understands. These are used by the PySide6 GUI to show or hide UI controls.
# Keys correspond to backend names, values are sets containing any of
# "voice", "lang", "rate", "seed" and "file".
BACKEND_FEATURES: dict[str, set[str]] = {
    "pyttsx3": {"voice", "lang", "rate"},
    "gtts": {"lang"},
    "bark": {"voice"},
    "tortoise": {"voice"},
    "edge_tts": {"voice", "rate"},
    "demucs": {"file"},
    "mms": {"lang"},
    "vocos": {"file"},
    "kokoro": {"voice", "rate", "seed"},
    "chatterbox": {"voice", "seed"},
}

_LOG_DIR = Path.home() / ".hybrid_tts"

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


def _get_distribution_name(package_spec: str) -> str:
    """Return the pip distribution name for the given requirement spec."""
    try:
        from packaging.requirements import Requirement

        req = Requirement(package_spec)
        name = req.name
    except Exception:
        # Fallback to a simple split if packaging is not available or parsing fails
        name = package_spec.split("@")[0].strip().split()[0]

    return name


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
        dist_name = _get_distribution_name(pkg)
        try:
            metadata.distribution(dist_name)
        except metadata.PackageNotFoundError:
            missing.append(pkg)
    return missing

def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)

def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        install_package_in_venv(missing)
        _log_action("install", name, missing)


def uninstall_backend(name: str) -> None:
    """Uninstall packages for the given backend if present."""
    packages = _get_backend_packages(name)
    if packages:
        uninstall_package_from_venv([_get_distribution_name(p) for p in packages])
        _log_action("uninstall", name, packages)


def _log_action(action: str, name: str, packages: list[str]) -> None:
    _LOG_DIR.mkdir(exist_ok=True)
    log_file = _LOG_DIR / "install.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {action} {name}: {', '.join(packages)}\n")

