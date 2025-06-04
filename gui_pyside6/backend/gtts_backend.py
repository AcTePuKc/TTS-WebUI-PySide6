from pathlib import Path
from gtts import gTTS


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    rate: int | None = None,
    voice: str | None = None,
    lang: str = "en",
) -> Path:

    """Synthesize speech using gTTS and save to an MP3 file."""
    tts = gTTS(text=text, lang=lang)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tts.save(str(output_path))
    return output_path
