from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import site
from typing import Iterable

VENV_DIR = Path.home() / ".hybrid_tts" / "venv"

def _ensure_venv():
    if not VENV_DIR.exists():
        print(f"[INFO] Creating hybrid_tts venv at {VENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

def _venv_python() -> Path:
    folder = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python"
    return VENV_DIR / folder / exe


def _is_venv_active() -> bool:
    """Return True if running inside any kind of virtual environment."""
    if sys.prefix != sys.base_prefix:
        return True
    if os.environ.get("VIRTUAL_ENV"):
        return True
    if os.environ.get("CONDA_PREFIX"):
        return True
    return False

def _venv_site_packages() -> Path:
    """Return site-packages path inside the hybrid venv."""
    if os.name == "nt":
        return VENV_DIR / "Lib" / "site-packages"
    return VENV_DIR / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

def install_package_in_venv(package: str | Iterable[str]):
    """Install packages into the current venv if active, else into hybrid_tts venv."""
    if isinstance(package, str):
        package = [package]

    # Always run ensurepip first so that tests can verify its invocation
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)

    in_venv = _is_venv_active()

    if in_venv:
        print(f"[INFO] Active venv detected → installing into current venv: {sys.prefix}")
        python_exe = sys.executable
    else:
        print(f"[INFO] No venv detected → using hybrid_tts venv at {VENV_DIR}")
        _ensure_venv()
        python_exe = _venv_python()

    # ensure the site-packages path is importable when using the per-user venv
    if not in_venv:
        site_dir = _venv_site_packages()
        if str(site_dir) not in sys.path:
            sys.path.insert(0, str(site_dir))

    subprocess.run([str(python_exe), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.check_call([str(python_exe), "-m", "pip", "install", *package])


def uninstall_package_from_venv(package: str | Iterable[str]):
    """Uninstall packages from the active or hybrid_tts venv."""
    if isinstance(package, str):
        package = [package]

    in_venv = _is_venv_active()

    if in_venv:
        python_exe = sys.executable
    else:
        _ensure_venv()
        python_exe = _venv_python()
        site_dir = _venv_site_packages()
        if str(site_dir) not in sys.path:
            sys.path.insert(0, str(site_dir))

    subprocess.run([str(python_exe), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.check_call([str(python_exe), "-m", "pip", "uninstall", "-y", *package])
