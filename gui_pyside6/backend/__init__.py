from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from ..utils.install_utils import install_package_in_venv
from .pyttsx_backend import synthesize_to_file
from .gtts_backend import synthesize_to_file as gtts_synthesize

BACKENDS = {
    "pyttsx3": synthesize_to_file,
    "gtts": gtts_synthesize,
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


def missing_backend_packages(name: str) -> list[str]:
    return [pkg for pkg in _get_backend_packages(name) if importlib.util.find_spec(pkg) is None]


def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)


def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        install_package_in_venv(missing)
