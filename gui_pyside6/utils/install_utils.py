from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable


VENV_DIR = Path.home() / ".hybrid_tts" / "venv"


def _ensure_venv():
    if not VENV_DIR.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_package_in_venv(package: str | Iterable[str]):
    _ensure_venv()
    if isinstance(package, str):
        package = [package]
    pip = VENV_DIR / "bin" / "pip"
    subprocess.check_call([str(pip), "install", *package])
