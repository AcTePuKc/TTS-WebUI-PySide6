# Hybrid TTS App - Planning

This document tracks the initial tasks for building the PySide6 Hybrid TTS application.

- Create `/gui_pyside6` folder with backend, utils and ui subpackages.
- Copy useful files from the existing `tts_webui` project to the new backend and utils.
- Implement minimal PySide6 GUI with a synthesize button and TTS backend dropdown.
- Add lazy installation utilities for optional backends.
- Provide a FastAPI server with a /synthesize endpoint that can be launched from the GUI.
- Added backend requirements mapping and automatic installation of missing packages when a backend is used.
- Include `requirements.uv.toml` for UV-based installs and an `install_torch.py` script for selecting the correct PyTorch build.
- Added a lightweight `Dockerfile.server` to run the FastAPI server as a container.
- Created `run_pyside.sh` and `run_pyside.bat` to launch the new GUI.
- Added dedicated `requirements.in` and `requirements.lock.txt` for the PySide6 GUI.
- Pruned extension packages from requirements and documented PySide6 launcher in README.
- Replaced extension-based backend requirements with real pip packages and added `mms_languages.txt` for the MMS backend.
- **Core requirements remain minimal.** `requirements.uv.toml` lists only the base
   dependencies (PySide6, FastAPI, PyTorch, etc.). Optional TTS extensions are
   specified in `backend_requirements.json` and installed on demand at runtime.
- Implemented an "Open Output Folder" button in the main window that opens the
  directory of the last synthesized file and uses the existing `open_folder`
  utility.
- Add a "Play Last Output" button that uses QtMultimedia to play the most
  recent WAV file directly in the application.
- Provide a speech rate selector so users can control the pyttsx3 output speed.
- Add a voice selector dropdown for pyttsx3 so users can pick from installed
  voices. Extend the API server to accept `voice` and `rate` parameters.
- Introduce a gTTS backend for simple online synthesis with MP3 output.
- Provide a language selector for gTTS so users can choose the output language.
- Add an "Install Backend" button so users can download optional dependencies
  when selecting a new backend.
- Install optional backends using the Python executable that launched the GUI so
  packages are added to the active environment regardless of whether a
  virtualenv is used.
- Import backend modules lazily so missing packages don't break startup.
- Ensure pip is available when installing optional backends by invoking
  `python -m ensurepip` before `pip install`. Also fix backend import errors by
  explicitly importing `importlib.util`.
- Persist optional backend install status in `~/.hybrid_tts/install.log` and load
  it on startup so the UI remembers previously installed backends.

