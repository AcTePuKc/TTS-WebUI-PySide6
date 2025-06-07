import subprocess
import sys
from pathlib import Path

if sys.platform == "darwin":

    def open_folder(folder_path: str):
        subprocess.check_call(["open", "--", folder_path])

elif sys.platform.startswith("linux"):

    def open_folder(folder_path: str):
        subprocess.check_call(["xdg-open", folder_path])

elif sys.platform == "win32":

    def open_folder(folder_path: str):
        subprocess.Popen(["explorer", folder_path])


LOG_DIR = Path.home() / ".hybrid_tts"

def open_log_dir():
    """Open the directory containing the application log file."""
    open_folder(str(LOG_DIR))


if __name__ == "__main__":
    # open_folder("./data/models/")
    import os

    open_folder(os.path.join(os.path.dirname(__file__), "..", "data", "models"))
