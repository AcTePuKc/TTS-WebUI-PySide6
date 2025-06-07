# Kokoro voice dropdown issue

During testing the Kokoro backend, the voice selector remained empty even after installing the backend.

**Findings**
- `list_voices()` imported `extension_kokoro.CHOICES`. Importing this package executes `extension_kokoro.__init__` which requires `gradio` and fails if it is not installed.
- `backend_requirements.json` listed `extension_kokoro_tts_api` as a required package for the `kokoro` backend. This package is unrelated to voice generation, so `is_backend_installed('kokoro')` returned `False` unless it was installed.

**Fixes implemented**
- `list_voices()` now loads `CHOICES.py` directly using `importlib.util.find_spec` and `exec` to avoid the `gradio` dependency.
- Removed the unnecessary `extension_kokoro_tts_api` entry and a duplicate `chatterbox` entry from `backend_requirements.json`.

With these changes the Kokoro voice list populates correctly once `extension_kokoro` is installed.

### Follow-up

The latest Kokoro releases ship as `kokoro-fastapi` and no longer expose a
`CHOICES` module. `list_voices()` now falls back to scanning the packaged
`voices` directory when `extension_kokoro` is missing.

### Follow-up 2

The fallback path originally used `Path(spec.origin).parent`, which resolved to
`kokoro_fastapi/` inside the package. The voice models reside one directory
higher under `api/src/voices/v1_0`. Adjusting the path to
`Path(spec.origin).parent.parent` restores voice detection for the FastAPI
package.

### Follow-up 3

`is_backend_installed('kokoro')` still returned `False` even after installing
`kokoro-fastapi` because the helper looked for an importable module name.
The package exposes its modules under generic names like `inference` and
`services` so `importlib.util.find_spec("kokoro_fastapi")` failed.  Installation
checks now rely on `importlib.metadata.distribution` to detect the presence of
the distribution regardless of module layout.

### Follow-up 4

Importing `extension_kokoro.main` still pulled in Gradio modules, causing a `No module named "gradio_iconbutton"` error during synthesis. The backend now implements its own Kokoro wrapper using the public `kokoro` library so no Gradio components are imported.

### Follow-up 5

Recent Kokoro releases were thought to rely on a `kokoro-fastapi` package. Voice packs were not detected because `backend_requirements.json` still referenced the legacy `kokoro` distribution. After testing, no `kokoro-fastapi` package was found on PyPI. Reverting to the `kokoro` requirement keeps voice detection working.

### Follow-up 6

The attempted switch to `kokoro-fastapi` caused backend installation errors since that distribution does not exist on PyPI. The metadata and requirements now reference `kokoro` again while `missing_backend_packages()` accepts either name for compatibility.

### Follow-up 7

Additional logging now confirms that `_synth_busy` switches to `True` when a
backend worker starts and back to `False` after `on_synthesize_finished()` runs.
Tests cover text edits and audio file loads to ensure
`update_synthesize_enabled()` executes in both cases. No new situations were
found where the **Synthesize** button stays disabled beyond earlier backend
exceptions interrupting the finish callback.

### Follow-up 8

The Kokoro project officially released the `kokoro` distribution on PyPI.
Previous versions required using the temporary `kokoro-fastapi` package.
Our backend metadata and requirements now depend on `kokoro` to match the
published package name.  Tests and installation helpers were updated accordingly.

