# Repository Guidelines

This repository hosts a PySide6-based TTS launcher. Core dependencies are kept minimal.

* `requirements.uv.toml` lists **only** the base packages needed to run the GUI and API server (PySide6, FastAPI, PyTorch, etc.).
* Optional TTS backends are declared in `gui_pyside6/backend/backend_requirements.json` and are installed lazily at runtime.
* The large `requirements.in`/`requirements.lock.txt` pair mirrors the original WebUI requirements for reference; however new extensions should not be added there unless strictly required for the GUI itself.
* The `run_pyside.sh` and `.bat` scripts create a venv using `uv`, compile `requirements.lock.txt`, install deps, and run the GUI.

When modifying code within this repo:

1. Keep `requirements.uv.toml` minimal.
2. Place optional backend packages in `backend_requirements.json`.
3. After code or requirement changes, run `pytest -q` and `uv pip compile requirements.in -o requirements.lock.txt`.

