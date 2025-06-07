from __future__ import annotations

from pathlib import Path


def _chunk_text(text: str) -> list[str]:
    """Split long text into manageable chunks."""
    try:
        from nltk.tokenize import sent_tokenize
    except Exception:
        # simple fallback
        sentences = text.replace("\n", " ").split(".")
    else:
        sentences = sent_tokenize(text)

    chunks: list[str] = []
    current = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(current) + len(sent) + 1 <= 280:
            current = f"{current} {sent}".strip()
        else:
            if len(current) >= 20:
                chunks.append(current)
                current = sent
            else:
                current = f"{current} {sent}".strip()
        while len(current) > 280:
            chunks.append(current[:280])
            current = current[280:]
    if current:
        chunks.append(current)
    return chunks


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

    all_chunks = []
    for part in _chunk_text(text):
        part_chunks = [c for c in tts.generate(part, exaggeration=exaggeration, cfg_weight=cfg_weight, temperature=temperature)]
        if not part_chunks:
            raise RuntimeError("Chatterbox failed to generate audio")
        all_chunks.extend(part_chunks)
    audio = torch.cat(all_chunks, dim=1).squeeze().cpu().numpy()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, tts.sr)
    return output_path


def list_voices() -> list[tuple[str, str]]:
    """Return bundled Chatterbox voice names and audio paths.

    Supports: WAV (recommended), MP3 (supported), AAC (experimental,
    may require ffmpeg-enabled backend).
    """

    package_dir = Path(__file__).resolve().parent.parent
    voices_dir = package_dir / "voices" / "chatterbox"
    result: list[tuple[str, str]] = []
    if voices_dir.exists():
        for audio_file in voices_dir.glob("*.*"):
            if audio_file.suffix.lower() in [".wav", ".mp3", ".aac"]:
                result.append((audio_file.stem, str(audio_file)))
    return result
