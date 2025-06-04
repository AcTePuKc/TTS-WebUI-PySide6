from __future__ import annotations

from pathlib import Path

# Bark is a heavy dependency that may not be installed by default.
# The backend_requirements.json maps the "bark" backend to
# `extension_bark` which provides the Bark TTS implementation.
# This backend provides a thin wrapper that calls the library if present.

def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    voice: str | None = None,
    history_prompt: str | None = None,
) -> Path:
    """Synthesize speech using the Bark library.

    Parameters
    ----------
    text: str
        Text to synthesize.
    output_path: Path
        Where to save the generated WAV file.
    voice: str | None, optional
        Voice identifier used by Bark. Defaults to the library's default voice.
    history_prompt: str | None, optional
        Optional history prompt to condition generation.
    """
    from bark import SAMPLE_RATE
    from bark.generation import generate_audio, preload_models
    import numpy as np
    import soundfile as sf

    # Bark requires models to be preloaded before generation.
    preload_models()

    waveform = generate_audio(text, history_prompt=history_prompt or voice)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ensure waveform is a 1D numpy array
    if isinstance(waveform, list):
        waveform = np.concatenate(waveform)

    sf.write(str(output_path), waveform, SAMPLE_RATE)
    return output_path
