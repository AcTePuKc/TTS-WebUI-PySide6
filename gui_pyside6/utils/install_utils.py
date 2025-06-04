from __future__ import annotations

import subprocess
import sys
from typing import Iterable


def install_package_in_venv(package: str | Iterable[str]):
    """Install packages into the environment running this process."""
    if isinstance(package, str):
        package = [package]
    subprocess.check_call([sys.executable, "-m", "pip", "install", *package])
