# Salvage Log

This file tracks files copied or cleaned during the migration to the PySide6 GUI.

- Created initial project structure under `/gui_pyside6`.
- Copied utility modules from `tts_webui/utils`:
  - `audio_array_to_sha256.py`
  - `torch_clear_memory.py`
  - `open_folder.py`
  - `create_base_filename.py`
- Added minimal lazy install helper in `gui_pyside6/utils/install_utils.py`.
- Created initial FastAPI server skeleton in `gui_pyside6/backend/api_server.py`.
- Added `backend_requirements.json` and `ensure_backend_installed` helper.
- Added `requirements.uv.toml` listing minimal dependencies for the new GUI.
- Core dependencies stay minimal. Optional TTS backends are listed in
  `backend_requirements.json` and installed lazily at runtime.
- Created `install_torch.py` helper to install PyTorch with optional CUDA. Moved it under `gui_pyside6/`.
- Added `Dockerfile.server` for running the FastAPI server.
- Added `backend_requirements.json` and `ensure_backend_installed` helper.
- Added `run_pyside.sh` and `run_pyside.bat` installer scripts for launching the GUI.
- Added standalone `requirements.in` and `requirements.lock.txt` so the GUI is independent of WebUI requirements.
- Pruned unused `extension_*` packages from `requirements.in` and regenerated the lock file.
- Added standalone `requirements.in` and `requirements.lock.txt` so the GUI is independent of WebUI requirements.
- Added an `Open Output Folder` button in the PySide6 UI to open the directory of
  the most recent synthesis result.
- Added a `Play Last Output` button using QtMultimedia so users can listen to
  the generated audio without leaving the app.
- Implemented a speech rate selector in the PySide6 UI and added an optional
  `rate` parameter to the `pyttsx_backend` so users can control synthesis speed.
- Added a voice selector dropdown that lists available pyttsx3 voices. The
  selected voice is passed through to the backend and the API server now accepts
  optional `rate` and `voice` parameters.
- Added a basic gTTS backend with lazy installation. MP3 files are generated
  when this backend is selected.
- Extended gTTS backend to support a language parameter and added a language
  selector in the GUI that becomes active when gTTS is chosen.
