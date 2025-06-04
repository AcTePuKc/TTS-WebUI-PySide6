# Salvage Log

This file tracks files copied or cleaned during the migration to the PySide6 GUI.

- Created initial project structure under `/gui_pyside6`.
- Copied utility modules from `tts_webui/utils`:
  - `audio_array_to_sha256.py`
  - `torch_clear_memory.py`
  - `open_folder.py`
  - `create_base_filename.py`
- Added minimal lazy install helper in `gui_pyside6/utils/install_utils.py`.
