# Contributing to Hybrid PySide6 TTS App

This document explains how to contribute to the Hybrid PySide6 app and where to document changes.

## Scope of Contributions

This project contains multiple apps:
- `/gui_pyside6/` → active Hybrid PySide6 TTS app (this is where you contribute)
- `/react_ui/` → React UI (separate project, do not touch)
- Legacy WebUI → root files (frozen, do not touch)

**Work only in `/gui_pyside6/`.**
Do not modify `/react_ui/` or root-level files.
The exception is the repository's root `tests/` directory, which holds automated tests and may be updated.

## Directory Layout of `/gui_pyside6/`
```
gui_pyside6/
├── backend/                  → TTS and audio backends
├── ui/                       → PySide6 GUI code
├── utils/                    → shared utility functions
├── notes/                    → backend\_categories.md, investigations, etc.
├── docs/                     → project documentation (index.md and future pages)
├── resources/                → UI translation files, language data
├── main.py                   → app entry point
├── AGENTS.md                 → project rules
├── README.md                 → app readme
├── planning.md               → project planning notes
├── SALVAGE_LOG.md            → files copied from other projects
├── investigation.md          → backend investigation notes
```

## Where to Document Changes

When adding or modifying code in `/gui_pyside6/`, document changes in the appropriate file:

| Change Type                          | Where to Document |
|--------------------------------------|-------------------|
| New backend added                    | `backend_categories.md`, `investigation.md` |
| Backend issue debugged / fixed       | `investigation.md` |
| Copied file from `tts_webui`         | `SALVAGE_LOG.md` |
| UI feature / behavior change         | `planning.md`, `investigation.md` if complex, `docs/ui_features.md` if user-facing |
| API feature or change                | `docs/api_usage.md`, `investigation.md` if complex |
| General project rules / architecture | `AGENTS.md` |
| General documentation                | `docs/index.md` or appropriate `docs/*.md` page |
| Anything unclear                     | Ask first, or document in `investigation.md` |


## Commit Guidelines

- Use clear commit messages.
- Do not silently add or remove backends — document in the appropriate `.md` files.
- Do not modify `tts_webui/`, `/react_ui/`, or root files.
- For backend-related changes, always update `backend_categories.md` and `investigation.md`.
- If you copy any utility code from WebUI, log it in `SALVAGE_LOG.md`.

## Backend Development Notes

- Backends live in `/gui_pyside6/backend/`.
- Optional backend packages are listed in `backend/backend_requirements.json`.
- Hybrid’s backend system is independent from WebUI — do not copy WebUI extension loaders.
- Maintain a flat, clean backend list.
- Implement new backends fully within `/gui_pyside6/backend/`.

## UI Layout Guidelines

- All backend-specific option groups must:

    - Be created at window init time (not dynamically later).
    - Be added consistently to the UI:

        - If simple, add to Parameters area layout.
        - If complex (e.g. Chatterbox Options), add to main layout *above* History area.

    - Be shown/hidden using `.setVisible()` depending on selected backend and available voices/parameters.

This ensures consistent UI layout and prevents widgets from appearing in unexpected order.

If adding a new backend, please follow this pattern.

## Workflow for Adding New Backends

1. Implement the backend in `/gui_pyside6/backend/`.
2. Add the backend to `backend/backend_requirements.json`.
3. Update `backend_categories.md`.
4. Test the backend and document findings or fixes in `investigation.md`.
5. If any files are copied from WebUI or other projects, record them in `SALVAGE_LOG.md`.
6. Commit with a clear, descriptive message.

## Summary

Work only inside `/gui_pyside6/`.  
Document what you change.  
When unsure where to document something, ask first or record it in `investigation.md`.

For project architecture and app rules, see `AGENTS.md`.

