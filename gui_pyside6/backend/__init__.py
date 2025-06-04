from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from .pyttsx_backend import synthesize_to_file
from ..utils.install_utils import install_package_in_venv
from .pyttsx_backend import synthesize_to_file

BACKENDS = {
    "pyttsx3": synthesize_to_file,
}


def available_backends():
    return list(BACKENDS.keys())


_REQ_FILE = Path(__file__).with_name("backend_requirements.json")


def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    if not _REQ_FILE.exists():
        return

    with _REQ_FILE.open() as f:
        reqs: dict[str, list[str]] = json.load(f)

    packages = reqs.get(name)
    if not packages:
        return

    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
    if missing:
        install_package_in_venv(missing)