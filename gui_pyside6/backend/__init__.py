from __future__ import annotations

import functools
import importlib
import importlib.util
from importlib import metadata
import json
import sys
from pathlib import Path


from datetime import datetime
from ..utils import install_utils
from ..utils.install_utils import uninstall_package_from_venv
import subprocess
from shutil import which

_METADATA_DIR = Path(__file__).with_name("metadata")
_BACKEND_METADATA: dict[str, dict[str, str]] = {}
if _METADATA_DIR.exists():
    try:
        import tomllib  # Python 3.11+

        for path in _METADATA_DIR.glob("*.toml"):
            with path.open("rb") as f:
                _BACKEND_METADATA[path.stem] = tomllib.load(f)
    except Exception:
        pass

def get_backend_repo(name: str) -> str | None:
    return _BACKEND_METADATA.get(name, {}).get("repo_url")

def get_backend_package(name: str) -> str | None:
    return _BACKEND_METADATA.get(name, {}).get("package")


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
    "whisper": {"file"},
}

# Short descriptions for each backend shown in the UI
BACKEND_INFO: dict[str, str] = {
    name: data.get("description", "") for name, data in _BACKEND_METADATA.items()
}

# Categorize backends for the PySide6 UI. Stable text-to-speech engines are
# listed separately from audio tools and experimental components.
TTS_BACKENDS = [
    "pyttsx3",
    "gtts",
    "edge_tts",
    "mms",
    "kokoro",
    "chatterbox",
]

# Tool backends operate on audio files rather than generating speech from text.
# Whisper is handled separately as a transcriber, so it should not be included
# in this list.
TOOL_BACKENDS = ["demucs", "vocos"]

EXPERIMENTAL_BACKENDS = ["bark", "tortoise"]

_LOG_DIR = Path.home() / ".hybrid_tts"
_INSTALL_LOG = _LOG_DIR / "install.log"

# Backends that have been installed previously according to the install log or
# current environment.  Populated at import time by ``load_persisted_installs``.
_INSTALLED_BACKENDS: set[str] = set()

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


def load_persisted_installs() -> None:
    """Populate ``_INSTALLED_BACKENDS`` from the install log and environment."""
    names: set[str] = set()
    if _INSTALL_LOG.exists():
        for line in _INSTALL_LOG.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                action, backend = parts[1], parts[2].rstrip(":")
                if action == "install":
                    names.add(backend)
                elif action == "uninstall":
                    names.discard(backend)

    # Also mark any backends whose packages are already available
    for backend in BACKENDS:
        if backend not in names and not missing_backend_packages(backend):
            names.add(backend)

    global _INSTALLED_BACKENDS
    _INSTALLED_BACKENDS = names


def backend_was_installed(name: str) -> bool:
    """Return True if the backend appears in the persisted install log."""
    return name in _INSTALLED_BACKENDS


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

def _dist_or_module_available(name: str) -> bool:
    """Return True if the distribution or importable module exists."""
    try:
        metadata.distribution(name)
        return True
    except metadata.PackageNotFoundError:
        pass
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def missing_backend_packages(name: str) -> list[str]:
    """Return a list of required packages that are not currently installed."""

    # The Kokoro backend ships under the ``kokoro`` distribution.
    if name == "kokoro" and _dist_or_module_available("kokoro"):
        return []

    missing = []
    for pkg in _get_backend_packages(name):
        dist_name = _get_distribution_name(pkg)
        if not _dist_or_module_available(dist_name):
            missing.append(pkg)
    return missing

def is_backend_installed(name: str) -> bool:
    return not missing_backend_packages(name)


# ---------------- installation helpers -----------------

# Backends that bundle PyTorch dependencies should be installed
# without dependency resolution so that the app's existing torch
# package is reused. These packages include:
# bark, chatterbox-tts, vocos, kokoro, tortoise-tts

_TORCH_BACKENDS = {"bark", "chatterbox", "vocos", "kokoro", "tortoise"}


def _uv_available() -> bool:
    """Return True if the ``uv`` command is available."""
    return which("uv") is not None


def _install_backend_packages(packages: list[str], *, no_deps: bool = False) -> None:
    """Install the given packages into the appropriate Python environment."""
    if isinstance(packages, str):
        packages = [packages]

    # Mirror logic from install_utils.install_package_in_venv
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)

    in_venv = install_utils._is_venv_active()

    if in_venv:
        python_exe = sys.executable
    else:
        install_utils._ensure_venv()
        python_exe = str(install_utils._venv_python())
        site_dir = install_utils._venv_site_packages()
        if str(site_dir) not in sys.path:
            sys.path.insert(0, str(site_dir))

    subprocess.run([str(python_exe), "-m", "ensurepip", "--upgrade"], check=True)

    if _uv_available():
        cmd = ["uv", "pip", "install", "-p", str(python_exe)]
    else:
        cmd = [str(python_exe), "-m", "pip", "install"]

    if no_deps:
        cmd.append("--no-deps")

    subprocess.check_call(cmd + packages)

def ensure_backend_installed(name: str) -> None:
    """Install packages required for the given backend if missing."""
    missing = missing_backend_packages(name)
    if missing:
        no_deps = name in _TORCH_BACKENDS
        _install_backend_packages(missing, no_deps=no_deps)
        _log_action("install", name, missing)
        _INSTALLED_BACKENDS.add(name)

def uninstall_backend(name: str) -> None:
    """Uninstall packages for the given backend if present."""
    packages = _get_backend_packages(name)
    if not packages:
        return

    # Determine which packages are still required by other installed backends
    used_by_others: set[str] = set()
    if _REQ_FILE.exists():
        with _REQ_FILE.open() as f:
            all_reqs: dict[str, list[str]] = json.load(f)
        for other, reqs in all_reqs.items():
            if other == name:
                continue
            if is_backend_installed(other):
                used_by_others.update(_get_distribution_name(p) for p in reqs)

    uninstall_list: list[str] = []
    skipped: list[str] = []
    for pkg in packages:
        dist = _get_distribution_name(pkg)
        if dist in used_by_others:
            skipped.append(pkg)
        else:
            uninstall_list.append(dist)

    if uninstall_list:
        uninstall_package_from_venv(uninstall_list)
        _log_action("uninstall", name, [p for p in packages if _get_distribution_name(p) in uninstall_list])
        _INSTALLED_BACKENDS.discard(name)

    if skipped:
        _log_action("skip_uninstall", name, skipped)


def _log_action(action: str, name: str, packages: list[str]) -> None:
    _LOG_DIR.mkdir(exist_ok=True)
    with _INSTALL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {action} {name}: {', '.join(packages)}\n")


# Initialize installed backend set on import
load_persisted_installs()
