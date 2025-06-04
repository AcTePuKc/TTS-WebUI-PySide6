from pathlib import Path
import subprocess
import sys
from datetime import datetime
from PySide6 import QtWidgets
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ..backend import (
    BACKENDS,
    available_backends,
    ensure_backend_installed,
    is_backend_installed,
)
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
        self.backend_combo.currentTextChanged.connect(self.on_backend_changed)
        layout.addWidget(self.backend_combo)

        # Install backend button
        self.install_button = QtWidgets.QPushButton("Install Backend")
        self.install_button.clicked.connect(self.on_install_backend)
        layout.addWidget(self.install_button)

        # Voice selector (pyttsx3 only)
        self.voice_combo = QtWidgets.QComboBox()
        self.voice_combo.setEnabled(False)
        layout.addWidget(self.voice_combo)

        # Language selector (gTTS only)
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.setEnabled(False)
        layout.addWidget(self.lang_combo)

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

        # Load voices for initial backend
        self.on_backend_changed(self.backend_combo.currentText())
        self.update_install_status()

    def on_synthesize(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status.setText("Please enter some text")
            return
        backend = self.backend_combo.currentText()
        if not is_backend_installed(backend):
            self.status.setText("Backend not installed. Click 'Install Backend' first.")
            return
        output = self._generate_output_path(text, backend)
        rate = self.rate_spin.value()
        voice_id = self.voice_combo.currentData()
        lang_code = self.lang_combo.currentData()
        BACKENDS[backend](
            text, output, rate=rate, voice=voice_id, lang=lang_code
        )
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

    def on_backend_changed(self, backend: str):
        self.update_install_status()
        if not is_backend_installed(backend):
            self.voice_combo.clear()
            self.voice_combo.setEnabled(False)
            self.lang_combo.clear()
            self.lang_combo.setEnabled(False)
            return

        if backend == "pyttsx3":
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
            except Exception:
                voices = []
            self.voice_combo.clear()
            self.voice_combo.addItem("(default)", None)
            for v in voices:
                name = getattr(v, "name", v.id)
                self.voice_combo.addItem(name, v.id)
            self.voice_combo.setEnabled(True)
            self.lang_combo.clear()
            self.lang_combo.setEnabled(False)
        else:
            self.voice_combo.clear()
            self.voice_combo.setEnabled(False)
            if backend == "gtts":
                try:
                    from gtts import lang
                    languages = lang.tts_langs()
                except Exception:
                    languages = {"en": "English"}
                self.lang_combo.clear()
                for code, name in languages.items():
                    self.lang_combo.addItem(f"{name} ({code})", code)
                self.lang_combo.setEnabled(True)
            else:
                self.lang_combo.clear()
                self.lang_combo.setEnabled(False)

    def _generate_output_path(self, text: str, backend: str) -> Path:
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = create_base_filename(text[:15], str(OUTPUT_DIR), backend, date)
        ext = ".mp3" if backend == "gtts" else ".wav"
        return Path(base + ext)

    def on_install_backend(self):
        backend = self.backend_combo.currentText()
        ensure_backend_installed(backend)
        self.update_install_status()
        # reload backend specific options
        self.on_backend_changed(backend)

    def update_install_status(self):
        backend = self.backend_combo.currentText()
        if is_backend_installed(backend):
            self.install_button.setEnabled(False)
            self.install_button.setText("Backend Installed")
        else:
            self.install_button.setEnabled(True)
            self.install_button.setText("Install Backend")
