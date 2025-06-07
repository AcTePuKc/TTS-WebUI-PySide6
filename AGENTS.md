# Repository Guidelines

This repository hosts three separate apps / UIs:

1. Legacy WebUI (Gradio-based) → root-level files → not maintained, frozen.
2. Hybrid PySide6-based TTS App → `/gui_pyside6/` → active project.
3. React-based Web UI → `/react_ui/` → separate project, not part of Hybrid PySide6.

## Hybrid PySide6 App Rules

- The Hybrid app is fully self-contained under `/gui_pyside6/`.
- All Hybrid development, files, and dependencies must stay under `/gui_pyside6/`.
- The top-level `/gui_pyside6/requirements.in`, `/gui_pyside6/requirements.lock.txt`, `/gui_pyside6/run_pyside6.bat`, `/gui_pyside6/run_pyside6.cs`,`/gui_pyside6/Dockerfile`, — are possible to be edited working on the Hybrid app.
- ANYTHING IN MAIN FOLDER IS FORBIDDEN TO EDIT and ONLY CAN BE TAKEN AS REFERENCE!
- The `tests/` folder at the repository root is used for automated testing and may be modified when adding or updating tests.
- The `/react_ui/` folder is a separate React-based UI — do not copy, modify, or merge React UI code into Hybrid PySide6.
- `gui_pyside6/requirements.uv.toml` lists only base packages.
- Optional TTS backends are declared in `gui_pyside6/backend/backend_requirements.json` and installed lazily.
- The Hybrid app has its own `/gui_pyside6/run_pyside6.sh` and `/gui_pyside6/run_pyside6.bat`.
- `/gui_pyside6/Dockerfile.server` belongs to `/gui_pyside6/`.
- Lazy backend installation must first detect if an active Python venv is in use.
    - If an active venv is detected (`sys.prefix != sys.base_prefix`), install backends into the active venv.
    - If no venv is active, install backends into a dedicated per-user venv at `~/.hybrid_tts/venv` (Windows: `C:\Users\USERNAME\.hybrid_tts\venv`).
- The `ensure_backend_installed()` helper must implement this logic to support both dev mode and packaged app mode.

## Extensions and Backend Metadata

- The Hybrid app is not an extension-based architecture like WebUI.
- The `/gui_pyside6/backend/backend_requirements.json` used in Hybrid is independent — do not try to reuse WebUI’s dynamic extension loading system.
- Maintain Hybrid’s `/gui_pyside6/backend_requirements.json` as a clean, minimal, flat list of optional backend packages.
- If adding new backends:
    - List them only in Hybrid’s `/gui_pyside6/backend/backend_requirements.json`.
    - Do not depend on `/extensions/` folders or WebUI extension loader patterns.
    - Implement backend support fully within `/gui_pyside6/backend/`.
- Hybrid app must remain standalone — no runtime dependency on WebUI extensions.
- If copying ideas or utility code from WebUI:
    - Clearly document what was copied and adapt it to Hybrid’s backend model.
    - Do not copy fragile WebUI extension hooks or Gradio dependencies.

## Workflow for Adding New Backends

1. Implement backend under `/gui_pyside6/backend/`.
2. Add the backend to `/gui_pyside6/backend/backend_requirements.json`.
3. Update `/gui_pyside6/backend_categories.md`.
4. Test and document any issues or findings in `investigation.md`.
5. Update `/gui_pyside6/Docs/index.md`
6. If files were copied from WebUI or other sources, summarize in `/gui_pyside6/SALVAGE_LOG.md`.
7. Commit with a clear message — avoid silent backend-related commits.

## Contributor Notes

- When adding new backends or features, always update `/gui_pyside6/backend_categories.md` and `/gui_pyside6/investigation.md` where applicable.
- Summarize file copies or cleanup in `/gui_pyside6/SALVAGE_LOG.md`.
- Use consistent commit messages so history is clear to all contributors.
- Do not attempt to merge Hybrid, React UI, and WebUI architectures — they are separate by design.
- For contribution workflow and where to document changes, see `/gui_pyside6/CONTRIBUTING.md`.

## Summary

The Hybrid PySide6 app is a separate, standalone project inside `/gui_pyside6/`.  
Work only in `/gui_pyside6/`.  
You may copy useful code from `tts_webui/`, but never modify `tts_webui/`, root files, or `/react_ui/` when building the Hybrid app.
