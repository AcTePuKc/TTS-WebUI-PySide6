from __future__ import annotations

from pathlib import Path


def separate_audio(
    audio_path: Path,
    output_dir: Path,
    *,
    model_name: str = "htdemucs",
) -> list[Path]:
    """Separate audio sources using the Demucs model.

    Parameters
    ----------
    audio_path: Path
        Input audio file to separate.
    output_dir: Path
        Directory where the separated stems will be saved.
    model_name: str, optional
        Name of the pretrained Demucs model to use.
    Returns
    -------
    list[Path]
        List of paths to the generated stem WAV files in order: drums, bass,
        other, vocals.
    """
    from demucs import pretrained
    from demucs.apply import apply_model
    from demucs.audio import AudioFile
    import torch
    import soundfile as sf

    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = pretrained.get_model(model_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    f = AudioFile(audio_path)
    wav = f.read(streams=0, samplerate=model.samplerate)
    wav = wav.mean(0)
    sources = apply_model(model, wav[None], device=device)[0]

    stems = []
    for name, tensor in zip(model.sources, sources):
        out_path = output_dir / f"{audio_path.stem}_{name}.wav"
        sf.write(out_path, tensor.cpu().numpy().T, model.samplerate)
        stems.append(out_path)
    return stems
