from __future__ import annotations

from pathlib import Path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    voice: str | None = None,
    device: str | None = None,
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5,
    temperature: float = 0.8,
    seed: int | None = None,
) -> Path:
    """Synthesize speech using the Chatterbox TTS library."""
    from chatterbox import ChatterboxTTS
    import torch
    import soundfile as sf

    if seed is not None:
        import random

        random.seed(seed)
        torch.manual_seed(seed)

    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    tts = ChatterboxTTS.from_pretrained(device)

    if voice:
        tts.prepare_conditionals(voice, exaggeration=exaggeration)
    else:
        voices = list_voices()
        if voices:
            tts.prepare_conditionals(voices[0][1], exaggeration=exaggeration)
        else:
            raise RuntimeError("No voice provided and no default voices found")

    chunks = [chunk for chunk in tts.generate(text, exaggeration=exaggeration, cfg_weight=cfg_weight, temperature=temperature)]
    if not chunks:
        raise RuntimeError("Chatterbox failed to generate audio")
    audio = torch.cat(chunks, dim=1).squeeze().cpu().numpy()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, tts.sr)
    return output_path


def list_voices() -> list[tuple[str, str]]:
    """Return bundled Chatterbox voice names and wav paths."""
    voices_dir = Path(__file__).resolve().parents[2] / "voices" / "chatterbox"
    result: list[tuple[str, str]] = []
    if voices_dir.exists():
        for wav in voices_dir.glob("*.wav"):
            result.append((wav.stem, str(wav)))
    return result
