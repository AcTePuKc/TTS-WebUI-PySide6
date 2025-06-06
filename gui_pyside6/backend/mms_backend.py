from __future__ import annotations

from pathlib import Path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    language: str = "eng",
    speaking_rate: float = 1.0,
    noise_scale: float = 0.667,
    noise_scale_duration: float = 0.8,
) -> Path:
    """Synthesize speech using the MMS TTS model from Facebook.

    Parameters
    ----------
    text: str
        Text to synthesize.
    output_path: Path
        Destination WAV file.
    language: str, optional
        ISO 639-3 language code, by default "eng".
    speaking_rate: float, optional
        Rate multiplier controlling speech speed.
    noise_scale: float, optional
        Noise scale parameter.
    noise_scale_duration: float, optional
        Noise scale duration parameter.
    """
    from transformers import VitsModel, VitsTokenizer
    import torch
    import soundfile as sf

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = VitsModel.from_pretrained(f"facebook/mms-tts-{language}").to(device)
    tokenizer = VitsTokenizer.from_pretrained(f"facebook/mms-tts-{language}")

    model.speaking_rate = speaking_rate
    model.noise_scale = noise_scale
    model.noise_scale_duration = noise_scale_duration

    inputs = tokenizer(text=text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    waveform = outputs.waveform[0].cpu().numpy().squeeze()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), waveform, model.config.sampling_rate)
    return output_path


def get_mms_languages() -> list[tuple[str, str]]:
    """Return list of available languages as (name, code) tuples."""
    try:
        from iso639 import Lang
        lang_file = Path(__file__).with_name("resources") / "mms_languages.txt"
        if lang_file.exists():
            with lang_file.open("r", encoding="utf-8") as f:
                codes = [line.strip() for line in f if line.strip()]
        else:
            codes = ["eng"]
        return [(Lang(code).name, code) for code in codes]
    except Exception:
        return [("English", "eng")]
