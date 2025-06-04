from pathlib import Path
import subprocess
import sys
from datetime import datetime
from PySide6 import QtWidgets
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

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

        # Speech rate selector
        rate_row = QtWidgets.QHBoxLayout()
        rate_label = QtWidgets.QLabel("Speech Rate:")
        self.rate_spin = QtWidgets.QSpinBox()
        self.rate_spin.setRange(50, 300)
        self.rate_spin.setValue(200)
        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.rate_spin)
        layout.addLayout(rate_row)

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

        # Play output button
        self.play_button = QtWidgets.QPushButton("Play Last Output")
        self.play_button.clicked.connect(self.on_play_output)
        self.play_button.setEnabled(False)
        layout.addWidget(self.play_button)

        self.api_process = None
        self.last_output: Path | None = None

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

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
        rate = self.rate_spin.value()
        BACKENDS[backend](text, output, rate=rate)
        self.last_output = output
        self.status.setText(f"Saved to {output}")
        self.play_button.setEnabled(True)

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

    def on_play_output(self):
        if self.last_output and self.last_output.exists():
            self.player.setSource(QUrl.fromLocalFile(str(self.last_output)))
            self.player.play()
        else:
            self.status.setText("No output file to play")

    def _generate_output_path(self, text: str, backend: str) -> Path:
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = create_base_filename(text[:15], str(OUTPUT_DIR), backend, date)
        return Path(base + ".wav")
