from __future__ import annotations

import asyncio
from pathlib import Path


async def _synthesize_async(text: str, output_path: Path, *, voice: str, rate: str, pitch: str | None) -> Path:
    from edge_tts import Communicate

    communicate = Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))
    return output_path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    voice: str = "en-US-GuyNeural",
    rate: str = "+0%",
    pitch: str | None = None,
) -> Path:
    """Synthesize speech using Microsoft Edge TTS service."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize_async(text, output_path, voice=voice, rate=rate, pitch=pitch))
    return output_path


async def _list_voices_async(locale: str | None = None) -> list[str]:
    """Return available Edge TTS voice names."""
    from edge_tts import list_voices

    voices = await list_voices()
    if locale:
        voices = [v for v in voices if v.get("Locale", "").startswith(locale)]
    return [v["ShortName"] for v in voices]


def list_voices(locale: str | None = None) -> list[str]:
    """Return available Edge TTS voices synchronously."""
    return asyncio.run(_list_voices_async(locale))
