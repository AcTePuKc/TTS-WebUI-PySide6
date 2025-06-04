from __future__ import annotations

from pathlib import Path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    voice: str = "random",
    preset: str = "fast",
) -> Path:
    """Synthesize speech using the Tortoise TTS library.

    Parameters
    ----------
    text: str
        Text to synthesize.
    output_path: Path
        Destination WAV file.
    voice: str, optional
        Voice identifier to use. Defaults to ``"random"``.
    preset: str, optional
        Generation preset to pass to ``tts_with_preset``.
    """
    from tortoise.api import TextToSpeech
    from tortoise.utils.audio import load_voices
    import numpy as np
    import soundfile as sf

    tts = TextToSpeech()
    voice_samples, conditioning_latents = load_voices([voice])

    result = tts.tts_with_preset(
        text,
        voice_samples=voice_samples,
        conditioning_latents=conditioning_latents,
        preset=preset,
    )

    tensor = result[0] if isinstance(result, list) else result
    audio = tensor.squeeze(0).cpu().t().numpy()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, 24000)
    return output_path
