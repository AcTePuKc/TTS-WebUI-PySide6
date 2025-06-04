# Repository Guidelines

This repository hosts THREE separate apps / UIs:

1️⃣ Legacy WebUI (Gradio-based) → root-level files → NOT maintained, frozen.  
2️⃣ Hybrid PySide6-based TTS App → `/gui_pyside6/` → ACTIVE project.  
3️⃣ React-based Web UI → `/react_ui/` → separate project → NOT part of Hybrid PySide6.

**Hybrid PySide6 app rules:**

* The Hybrid app is fully self-contained under `/gui_pyside6/`.  
* All Hybrid development, files, and dependencies MUST stay under `/gui_pyside6/`.  
* The top-level `requirements.in`, `requirements.lock.txt`, `run.bat`, `Dockerfile`, and other root-level files are **LEGACY** — do NOT edit them when working on the Hybrid app.  
* The `/react_ui/` folder is a **separate React-based UI** — DO NOT copy, modify, or merge React UI code into Hybrid PySide6.  
* `gui_pyside6/requirements.uv.toml` lists **only** base packages.
* Optional TTS backends declared in `gui_pyside6/backend/backend_requirements.json`, installed lazily.
* The Hybrid app has its own `run_pyside6.sh` and `run_pyside6.bat` inside `/gui_pyside6/`.
* `Dockerfile.server` belongs to `/gui_pyside6/`.
* Lazy backend installation MUST first detect if an active Python venv is in use.
    * If an active venv is detected (sys.prefix != sys.base_prefix), install backends into the active venv.
    * If no venv is active, install backends into a dedicated per-user venv at `~/.hybrid_tts/venv` (Windows: `C:\Users\USERNAME\.hybrid_tts\venv`).
* The `ensure_backend_installed()` helper MUST implement this logic to support both dev mode and packaged app mode.

**IMPORTANT:**  
When adding new features to the Hybrid app:  
✅ You MAY **COPY** utility code from `tts_webui/` or other folders — but you MUST NOT edit or move original `tts_webui/` files.  
✅ You MAY NOT copy or merge `/react_ui/` code into Hybrid PySide6 — they are separate architectures.  
✅ All Hybrid app code and refactored utilities MUST go inside `/gui_pyside6/`.  
✅ Do NOT attempt to "merge" Hybrid, React UI, and WebUI architectures — they are separate.

**Summary:**  
The Hybrid PySide6 app is a separate, standalone project inside `/gui_pyside6/`.  
Work ONLY in `/gui_pyside6/`.  
You may COPY useful code from `tts_webui/`, but NEVER modify `tts_webui/`, root files, or `/react_ui/` when building the Hybrid app.

