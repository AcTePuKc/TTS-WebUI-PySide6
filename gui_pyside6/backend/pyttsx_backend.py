import pyttsx3
from pathlib import Path


def synthesize_to_file(
    text: str,
    output_path: Path,
    *,
    rate: int | None = None,
    voice: str | None = None,
    lang: str | None = None,

) -> Path:
    """Synthesize speech using pyttsx3 and save to a WAV file."""
    engine = pyttsx3.init()
    if rate is not None:
        engine.setProperty("rate", rate)
    if voice is not None:
        engine.setProperty("voice", voice)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return output_path
