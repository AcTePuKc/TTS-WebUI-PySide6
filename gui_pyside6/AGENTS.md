# Repository Guidelines

This repository hosts TWO separate apps:

1️⃣ Legacy WebUI (Gradio-based) → top-level files → NOT maintained, frozen.  
2️⃣ Hybrid PySide6-based TTS App → **/gui_pyside6/** → ACTIVE project.

**Hybrid PySide6 app rules:**

* `gui_pyside6/requirements.uv.toml` lists **only** base packages.
* Optional TTS backends declared in `gui_pyside6/backend/backend_requirements.json`, installed lazily.
* The top-level `requirements.in` / `requirements.lock.txt` are **legacy** — do NOT edit them for PySide6.
* The Hybrid app has its own `run_pyside6.sh` and `.bat` **inside /gui_pyside6/**.
* Dockerfile.server belongs to `/gui_pyside6` — not top-level.
* The Hybrid app builds its own Docker image.

**Summary:** The Hybrid app is fully self-contained under `/gui_pyside6/`. We can reuse code from `tts_webui/` or other folders, but we do not modify the old WebUI or its root-level files. All Hybrid development stays inside `/gui_pyside6/`.