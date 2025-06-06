from __future__ import annotations

from pathlib import Path


def transcribe_to_text(
    audio_path: Path,
    *,
    model_name: str = "openai/whisper-small",
    return_timestamps: bool | None = None,
) -> str:
    """Transcribe speech from ``audio_path`` using a Whisper model.

    Parameters
    ----------
    audio_path:
        Path to an audio file supported by ``transformers``.
    model_name:
        HuggingFace model identifier.
    return_timestamps:
        If ``None``, automatically enable timestamps when the input audio
        duration is greater than 30 seconds. Otherwise, explicitly pass
        ``True`` or ``False`` to control timestamp generation.
    Returns
    -------
    str
        Transcribed text output.
    """
    from transformers import pipeline
    import torch

    if return_timestamps is None:
        duration = 0.0
        try:
            import soundfile as sf

            info = sf.info(str(audio_path))
            duration = info.frames / float(info.samplerate)
        except Exception:
            try:
                import torchaudio

                info = torchaudio.info(str(audio_path))
                duration = info.num_frames / float(info.sample_rate)
            except Exception:
                duration = 0.0
        return_timestamps = duration > 30.0

    device = 0 if torch.cuda.is_available() else -1
    pipe = pipeline(
        "automatic-speech-recognition", model=model_name, device=device
    )
    result = pipe(str(audio_path), return_timestamps=return_timestamps)
    if isinstance(result, dict):
        return result.get("text", "")
    return str(result)
