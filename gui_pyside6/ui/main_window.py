from pathlib import Path
import subprocess
import sys
from datetime import datetime
from PySide6 import QtWidgets

from ..backend import BACKENDS, available_backends, ensure_backend_installed
from ..utils.create_base_filename import create_base_filename
from ..utils.open_folder import open_folder

OUTPUT_DIR = Path("outputs")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 TTS Launcher")
        self.resize(400, 200)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QVBoxLayout(central)

        # Text input
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setPlaceholderText("Enter text to synthesize...")
        layout.addWidget(self.text_edit)

        # Backend dropdown
        self.backend_combo = QtWidgets.QComboBox()
        self.backend_combo.addItems(available_backends())
        layout.addWidget(self.backend_combo)

        # Synthesize button
        self.button = QtWidgets.QPushButton("Synthesize")
        self.button.clicked.connect(self.on_synthesize)
        layout.addWidget(self.button)

        # API server button
        self.api_button = QtWidgets.QPushButton("Run API Server")
        self.api_button.clicked.connect(self.on_api_server)
        layout.addWidget(self.api_button)

        # Open output folder button
        self.open_button = QtWidgets.QPushButton("Open Output Folder")
        self.open_button.clicked.connect(self.on_open_output)
        layout.addWidget(self.open_button)

        self.api_process = None
        self.last_output: Path | None = None

        # Status label
        self.status = QtWidgets.QLabel()
        layout.addWidget(self.status)

    def on_synthesize(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status.setText("Please enter some text")
            return
        backend = self.backend_combo.currentText()
        ensure_backend_installed(backend)
        output = self._generate_output_path(text, backend)
        BACKENDS[backend](text, output)
        self.last_output = output
        self.status.setText(f"Saved to {output}")

    def on_api_server(self):
        if self.api_process is None:
            ensure_backend_installed("api_server")
            self.api_process = subprocess.Popen(
                [sys.executable, "-m", "gui_pyside6.backend.api_server"]
            )
            self.api_button.setText("API Server Running...")
            self.api_button.setEnabled(False)
            self.status.setText("API server started at http://127.0.0.1:8000")
        else:
            self.status.setText("API server already running")

    def on_open_output(self):
        folder = self.last_output.parent if self.last_output else OUTPUT_DIR
        open_folder(str(folder))

    def _generate_output_path(self, text: str, backend: str) -> Path:
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = create_base_filename(text[:15], str(OUTPUT_DIR), backend, date)
        return Path(base + ".wav")
