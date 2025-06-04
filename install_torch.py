"""Install PyTorch with CUDA if available, otherwise CPU version."""
import subprocess
import sys


def has_nvidia_gpu() -> bool:
    try:
        subprocess.check_call(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def main() -> None:
    index = "https://download.pytorch.org/whl/cu118" if has_nvidia_gpu() else "https://download.pytorch.org/whl/cpu"
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--index-url",
        index,
        "torch",
        "torchvision",
        "torchaudio",
    ])


if __name__ == "__main__":
    main()
