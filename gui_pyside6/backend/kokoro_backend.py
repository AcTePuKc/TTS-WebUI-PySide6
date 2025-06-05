from __future__ import annotations

from pathlib import Path
import site


_MODELS: dict[tuple[str, bool], object] = {}
_PIPELINES: dict[str, object] = {}
_VOICES: dict[str, object] = {}


def _get_model(model_name: str, use_gpu: bool):
    from kokoro import KModel
    import torch

    gpu = bool(use_gpu and torch.cuda.is_available())
    key = (model_name, gpu)
    if key not in _MODELS:
        from kokoro import model as kokoro_model
        kokoro_model.KModel.REPO_ID = model_name
        model = KModel().to("cuda" if gpu else "cpu").eval()
        _MODELS[key] = model
    return _MODELS[key]


def _get_pipeline(lang_code: str):
    from kokoro import KPipeline

    if lang_code not in _PIPELINES:
        _PIPELINES[lang_code] = KPipeline(lang_code=lang_code, model=False)
    return _PIPELINES[lang_code]


def _get_voice(voice_name: str):
    if voice_name not in _VOICES:
        pipeline = _get_pipeline(voice_name[0])
        _VOICES[voice_name] = pipeline.load_voice(voice_name)
    return _VOICES[voice_name]


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
    import torch
    import soundfile as sf
    import random

    if seed is not None:
        random.seed(seed)
        torch.manual_seed(seed)

    speed = (rate / 200) if rate else 1.0
    if use_gpu is None:
        use_gpu = torch.cuda.is_available()

    model = _get_model(model_name, use_gpu)
    pipeline = _get_pipeline(voice[0])
    pack = _get_voice(voice)

    audio_parts = []
    for _, ps, _ in pipeline(text, voice, speed):
        ref_s = pack[len(ps) - 1]
        audio = model(ps, ref_s, speed)
        audio_parts.append(audio.cpu())

    if not audio_parts:
        raise RuntimeError("Kokoro TTS did not return audio")

    audio = torch.cat(audio_parts, dim=-1).squeeze().numpy()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, 24000)
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
                if voices:
                    return [(v, v) for v in sorted(voices)]
    except Exception:
        pass

    # Fallback: search all site-packages locations
    for root in site.getsitepackages():
        voice_dir = Path(root) / "api" / "src" / "voices" / "v1_0"
        if voice_dir.exists():
            voices = [p.stem for p in voice_dir.glob("*.pt")]
            if voices:
                return [(v, v) for v in sorted(voices)]
    return []
