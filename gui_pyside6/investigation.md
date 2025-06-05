# Kokoro voice dropdown issue

During testing the Kokoro backend, the voice selector remained empty even after installing the backend.

**Findings**
- `list_voices()` imported `extension_kokoro.CHOICES`. Importing this package executes `extension_kokoro.__init__` which requires `gradio` and fails if it is not installed.
- `backend_requirements.json` listed `extension_kokoro_tts_api` as a required package for the `kokoro` backend. This package is unrelated to voice generation, so `is_backend_installed('kokoro')` returned `False` unless it was installed.

**Fixes implemented**
- `list_voices()` now loads `CHOICES.py` directly using `importlib.util.find_spec` and `exec` to avoid the `gradio` dependency.
- Removed the unnecessary `extension_kokoro_tts_api` entry and a duplicate `chatterbox` entry from `backend_requirements.json`.

With these changes the Kokoro voice list populates correctly once `extension_kokoro` is installed.
