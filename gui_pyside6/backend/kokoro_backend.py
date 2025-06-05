from __future__ import annotations

from pathlib import Path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    voice: str = "af_heart",
    rate: int | None = None,
    model_name: str = "hexgrad/Kokoro-82M",
    use_gpu: bool | None = None,
    seed: int | None = None,
) -> Path:
    """Synthesize speech using the Kokoro TTS library."""
    from extension_kokoro.main import tts
    import torch
    import soundfile as sf
    import random

    if seed is not None:
        random.seed(seed)
        torch.manual_seed(seed)

    speed = (rate / 200) if rate else 1.0
    if use_gpu is None:
        use_gpu = torch.cuda.is_available()

    result = tts(
        text=text,
        voice=voice,
        speed=speed,
        use_gpu=use_gpu,
        model_name=model_name,
    )
    audio_out = result.get("audio_out")
    if not audio_out:
        raise RuntimeError("Kokoro TTS did not return audio")
    sample_rate, audio = audio_out

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, sample_rate)
    return output_path


def list_voices() -> list[tuple[str, str]]:
    """Return available Kokoro voice display names and identifiers."""
    try:
        from extension_kokoro import CHOICES as choices_mod
        return list(getattr(choices_mod, "CHOICES", {}).items())
    except Exception:
        pass

    try:
        import importlib.util
        from pathlib import Path
        spec = importlib.util.find_spec("extension_kokoro")
        if spec and spec.origin:
            choices_path = Path(spec.origin).parent / "CHOICES.py"
            if choices_path.exists():
                namespace: dict[str, object] = {}
                with choices_path.open("r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, namespace)
                choices = namespace.get("CHOICES", {})
                if isinstance(choices, dict):
                    return list(choices.items())
    except Exception:
        pass

    # Kokoro-FastAPI packages voice models under api/src/voices/v1_0
    try:
        import importlib.util
        spec = importlib.util.find_spec("kokoro_fastapi")
        if spec and spec.origin:
            base = Path(spec.origin).parent.parent
            voice_dir = base / "api" / "src" / "voices" / "v1_0"
            if voice_dir.exists():
                voices = [p.stem for p in voice_dir.glob("*.pt")]
                return [(v, v) for v in sorted(voices)]
    except Exception:
        pass
    return []
