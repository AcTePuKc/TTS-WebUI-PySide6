import os
import re
from typing import Optional


def _create_base_filename(
    title: Optional[str], output_path: str, model: str, date: str
) -> str:
    base = f"{date}__{model}__{replace_path_sep(title)}"
    return os.path.join(output_path, base, base)


def create_base_filename(
    title: Optional[str], output_path: str, model: str, date: str
) -> str:
    base_filename = _create_base_filename(title, output_path, model, date)

    base_directory = os.path.dirname(base_filename)
    os.makedirs(base_directory, exist_ok=True)

    return base_filename


def replace_path_sep(title: Optional[str]) -> str:
    """Return a filename-friendly snippet for the given title."""
    if title is None:
        return "None"

    sanitized = title.strip().replace(os.path.sep, "_")
    # Allow only common filename characters
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", sanitized)

    return sanitized or "None"
