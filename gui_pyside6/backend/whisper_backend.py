from __future__ import annotations

from pathlib import Path


def transcribe_to_text(
    audio_path: Path,
    *,
    model_name: str = "openai/whisper-large-v3",
) -> str:
    """Transcribe speech from ``audio_path`` using a Whisper model.

    Parameters
    ----------
    audio_path:
        Path to an audio file supported by ``transformers``.
    model_name:
        HuggingFace model identifier.
    Returns
    -------
    str
        Transcribed text output.
    """
    from transformers import pipeline
    import torch

    device = 0 if torch.cuda.is_available() else -1
    pipe = pipeline("automatic-speech-recognition", model=model_name, device=device)
    result = pipe(str(audio_path))
    if isinstance(result, dict):
        return result.get("text", "")
    return str(result)
