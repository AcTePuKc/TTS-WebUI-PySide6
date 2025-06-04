# Backend Parameter Mismatch Investigation (2025-06-04)

## Observed errors
- Running the PySide6 GUI with various backends caused multiple `TypeError` exceptions.
- Example trace from the logs when invoking `gtts` after installation:
  `TypeError: synthesize_to_file() got an unexpected keyword argument 'rate'`.
- Similar errors occurred for `edge_tts`, `demucs`, `tortoise`, `mms`, and `vocos` backends.
- Initial run with `pyttsx3` failed due to missing `pywintypes` module, which is part of `pywin32`.

## Cause
- `MainWindow.on_synthesize` unconditionally calls backend functions with `rate`, `voice`, and `lang` keyword arguments.
- Only the `pyttsx3` and `gtts` backends declare these parameters. Other backends have different signatures.
- When a backend does not accept one of these keywords, Python raises `TypeError`.
- Lines 116-120 in `ui/main_window.py` show the unconditional call:
  ```python
  rate = self.rate_spin.value()
  voice_id = self.voice_combo.currentData()
  lang_code = self.lang_combo.currentData()
  BACKENDS[backend](text, output, rate=rate, voice=voice_id, lang=lang_code)
  ```
- Backends like `pyttsx_backend` and `gtts_backend` accept these parameters, but `edge_tts_backend` and others do not.

## Recommended changes
- Adjust `on_synthesize` so it only passes parameters supported by the selected backend.
  - For example, pass `lang` only for `gtts` and possibly `mms`.
  - Pass `voice` for backends that support voice selection (`pyttsx3`, `edge_tts`).
  - Pass `rate` only where applicable (`pyttsx3`, `edge_tts`, `gtts`).
- Update the GUI to enable/disable widgets depending on the current backend. This is partially implemented but does not control parameter passing.
- While synthesis is running, disable the **Synthesize** button to prevent duplicate requests and gray it out. Re-enable it when synthesis completes or fails.
- Add a **Stop** button next to the playback controls to stop the currently playing audio via `QMediaPlayer.stop()`.
- Consider truncating or warning about very long text inputs to avoid accidentally passing extremely long strings to backends.

These adjustments should eliminate the runtime `TypeError` issues and improve the overall user experience.

## Follow-up 2025-06-04

Implemented dynamic parameter handling in `MainWindow.on_synthesize` so that only
supported keywords are passed to each backend. The synthesize button is now
automatically disabled when no text is entered, the selected backend is not
installed, or synthesis is currently running. Console messages indicate when
synthesis starts and finishes. Further improvements such as a dedicated stop
button are still pending.

## Follow-up 2025-06-05

Errors raised inside a backend prevented the final `update_synthesize_enabled()`
call from executing. As a result the **Synthesize** button stayed disabled after
a failure and the GUI had to be restarted. The `on_synthesize` method now wraps
the backend call in a `try/except/finally` block so the busy flag is always
cleared and the button state recovers even if synthesis fails.
