import pyttsx3
from pathlib import Path


def synthesize_to_file(text: str, output_path: Path) -> Path:
    """Synthesize speech using pyttsx3 and save to a WAV file."""
    engine = pyttsx3.init()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return output_path
