
# Hybrid PySide6 TTS App - Documentation Index

Welcome to the documentation for the Hybrid PySide6 TTS App.

This project is a standalone TTS and audio processing application with a native PySide6 GUI, optional FastAPI server, and modular backend support.

## Project Structure

```

/gui_pyside6/
├── backend/                  → TTS and audio backends
├── ui/                       → PySide6 GUI code
├── utils/                    → shared utility functions
├── notes/                    → backend\_categories.md, investigation.md, planning.md
├── resources/                → UI translation files and language data
├── main.py                   → application entry point
├── AGENTS.md                 → project rules and guidelines
├── CONTRIBUTING.md           → contributor workflow
├── planning.md               → project planning notes
├── investigation.md          → backend investigations
├── backend_categories.md     → backend feature categories
├── SALVAGE_LOG.md            → copied utility files log

```

## API Documentation

- The app includes an optional FastAPI server for programmatic synthesis.

- Start the server using **Run API Server** button in the GUI.
- API docs available at [http://localhost:8000/docs](http://localhost:8000/docs) when server is running.

## Transcription

When you choose a transcription backend such as **Whisper**, the
**Synthesize** button changes to **Transcribe**. Load an audio file and use
this button to generate text. Transcription backends require using the
Transcribe button.

See also:
- [API usage notes](#api-usage-notes) (future section)

## Developer Notes

- **Primary development happens inside `/gui_pyside6/`.**
- The React UI (`/react_ui/`) and legacy WebUI are separate and not maintained here.
- Backends should be implemented under `/gui_pyside6/backend/`.
- Optional backends listed in `backend/backend_requirements.json`.
- Backend and UI-related changes should be documented in the appropriate `.md` files (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Set `HYBRID_TTS_ALWAYS_ENABLE=1` in the environment to force the **Synthesize**,
  **Transcribe**, and **Process** buttons to stay enabled regardless of input
  state.

## Documentation Sections

- [Getting Started](getting_started.md) (setup, running the app)
- [Backends](backends.md) (current backends, supported features)
- [UI Features](ui_features.md) (overview of the GUI)
- [API Usage](api_usage.md) (details on the FastAPI server and endpoints)
- [Contribution Workflow](../CONTRIBUTING.md)
- [Project Guidelines](../AGENTS.md)

### Debug Logging

Run the app with debug logging enabled to help diagnose issues. Set the
`HYBRID_TTS_DEBUG` variable **before** launching the program:

```bash
HYBRID_TTS_DEBUG=1 python -m gui_pyside6.main
```

On Windows, set the variable and then run the command:

- **Command Prompt**

  ```cmd
  set HYBRID_TTS_DEBUG=1 && python -m gui_pyside6.main
  ```

- **PowerShell**

  ```powershell
  $env:HYBRID_TTS_DEBUG=1; python -m gui_pyside6.main
  ```

Logs are written to `~/.hybrid_tts/app.log` and can clarify problems with UI
state, such as the **Synthesize** button remaining disabled.

## Notes and Investigations

- [Investigation Notes](../investigation.md)
- [Backend Categories](../backend_categories.md)
- [Planning Notes](../planning.md)
- [SALVAGE_LOG](../SALVAGE_LOG.md)

---

## Status

The Hybrid PySide6 TTS app is under active development.  
The documentation is being expanded as the project evolves.
