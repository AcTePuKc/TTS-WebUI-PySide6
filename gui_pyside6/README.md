# Hybrid PySide6 TTS Application

This folder contains the actively developed PySide6 interface for offline text to speech (TTS). The repository also includes a legacy Gradio WebUI and a separate React-based web UI, but those projects live outside of this directory and are not maintained here.

## Project Layout

- **Legacy WebUI** – root level files in the repository. Frozen and not maintained.
- **Hybrid PySide6 App** – all source code under `/gui_pyside6/` (this folder). Active development happens here.
- **React Web UI** – located in `/react_ui/`, developed separately.

All Hybrid app code, scripts and dependencies stay inside `/gui_pyside6/`. Do not modify the legacy WebUI or the React UI when working on the PySide6 app.

## Installing and Running

1. Install **Python 3.11** and the [`uv`](https://github.com/astral-sh/uv) package.
2. Run `run_pyside.sh` (Linux/macOS) or `run_pyside.bat` (Windows) from this directory.
   The script creates a virtual environment, installs `requirements.uv.toml`,
   optionally installs PyTorch, and launches the GUI from the repository root.
3. You can also start the GUI manually (from the repository root) with:

   ```bash
   python -m gui_pyside6.main
   ```

When launched outside any virtual environment, the application automatically
adds the per-user environment at `~/.hybrid_tts/venv` to `sys.path` so packages
installed there remain available between sessions.

Optional TTS backends are installed on demand. Select a backend and click the **Install Backend** button if prompted.

Backend packages are defined in `backend/backend_requirements.json`. Installation first checks if the app is running inside a virtual environment; if so, packages install there. Detection now also considers `VIRTUAL_ENV` or `CONDA_PREFIX` environment variables so Conda and other managers work. If no environment is active, packages install into a per-user environment at `~/.hybrid_tts/venv` (`C:\Users\USERNAME\.hybrid_tts\venv` on Windows).
Metadata files under `backend/metadata/` record the primary package name and repository URL for each backend.

## Features

- Lazy installation of backends such as **pyttsx3** and **gTTS**.
- Experimental support for **Tortoise TTS** voice cloning.
- Online synthesis via **Edge TTS**.
- Voice and language selectors (when supported by the backend).
- Adjustable speech rate.
- "Play Last Output" and "Open Output Folder" buttons.
- Optional FastAPI server for programmatic synthesis.
- Experimental audio reconstruction with **Vocos**.
- Music source separation with **Demucs**. Load an audio file and the backend
  generates individual stem tracks.
- Speech-to-text transcription with **OpenAI Whisper**.
- When a transcription backend is selected, the **Synthesize** button becomes
  **Transcribe**. Load an audio file and use this button to convert speech to
  text. Tools like Whisper require the Transcribe button.
- Some tools may output a folder of audio files instead of a single file. The
  application adds the folder path to the history list and treats the first file
  as the last output.
- Optional UI translations. Place custom `.qm` and `.json` files under
  `~/.hybrid_tts/translations`.

## Preferences

Open **Edit → Preferences** to configure the application.

- **Auto play after synthesis** – automatically play generated audio.
- **Output directory** – folder where synthesized files are saved. Defaults to `outputs/`.
- **Uninstall Backends** – remove optional TTS backends you previously installed.

Custom translation files can be placed in `~/.hybrid_tts/translations` to
augment the UI language list.

Your settings are stored in `~/.hybrid_tts/preferences.json`.

## API Server

Click **Run API Server** in the main window to start a FastAPI service. By default
it listens on port `8000`. Visit `http://localhost:8000/docs` in your browser to
try the interactive API. You can change the listening port via **Edit →
Preferences** under "API server port". If the server fails to start, check for
port conflicts using `netstat -ano` on Windows or `lsof -i :<port>` on
Linux/macOS.

## Troubleshooting

- On Windows, the **pyttsx3** backend may fail with `ModuleNotFoundError: No module named 'pywintypes'`.
  Reinstalling `pywin32` inside the virtual environment usually resolves the issue:

  ```bash
  pip install --force-reinstall pywin32
  ```

- The **Demucs** backend requires the `ffmpeg` command and a valid audio file
  input. Use the **Load Audio File** button before synthesizing. The generated
  stem files appear in a new folder under `outputs/`.

## Running Tests

From the repository root, run:

```bash
pytest -q
```

Tests cover backend installation helpers and the API server.

## Development Guidelines

- Keep all new files and dependencies inside `/gui_pyside6/`.
- `requirements.uv.toml` lists only base packages; optional backends are listed in `backend/backend_requirements.json`.
- You may copy utility code from other folders but do **not** modify the legacy WebUI or React UI projects.

