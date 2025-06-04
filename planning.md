# Hybrid TTS App - Planning

This document tracks the initial tasks for building the PySide6 Hybrid TTS application.

- Create `/gui_pyside6` folder with backend, utils and ui subpackages.
- Copy useful files from the existing `tts_webui` project to the new backend and utils.
- Implement minimal PySide6 GUI with a synthesize button and TTS backend dropdown.
- Add lazy installation utilities for optional backends.
- Provide a FastAPI server with a /synthesize endpoint that can be launched from the GUI.
