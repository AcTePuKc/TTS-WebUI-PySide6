from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


VENV_DIR = Path.home() / ".hybrid_tts" / "venv"


def _ensure_venv():
    if not VENV_DIR.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])


def _venv_python() -> Path:
    folder = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python"
    return VENV_DIR / folder / exe


def install_package_in_venv(package: str | Iterable[str]):
    _ensure_venv()
    if isinstance(package, str):
        package = [package]
    python_exe = _venv_python()
    subprocess.check_call([str(python_exe), "-m", "pip", "install", *package])
