from __future__ import annotations

from pathlib import Path


def reconstruct_audio(
    audio_path: Path,
    output_path: Path,
    *,
    bandwidth: int = 0,
    model_name: str = "charactr/vocos-encodec-24khz",
) -> Path:
    """Reconstruct audio using the Vocos neural codec.

    Parameters
    ----------
    audio_path: Path
        Input audio file to process.
    output_path: Path
        Destination WAV file.
    bandwidth: int, optional
        Bandwidth level index. Defaults to ``0`` which corresponds to
        1.5 kbps. Higher values use more bandwidth and yield higher quality.
    model_name: str, optional
        HuggingFace model identifier. ``charactr/vocos-encodec-24khz`` by default.
    """
    import torch
    import torchaudio
    from vocos import Vocos

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vocos = Vocos.from_pretrained(model_name).to(device)

    waveform, sr = torchaudio.load(str(audio_path))
    if waveform.size(0) > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    waveform = torchaudio.functional.resample(waveform, orig_freq=sr, new_freq=24000)
    waveform = waveform.to(device)

    with torch.no_grad():
        bandwidth_id = torch.tensor([bandwidth], device=device)
        output = vocos(waveform, bandwidth_id=bandwidth_id)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(output_path), output.cpu(), 24000)
    return output_path
