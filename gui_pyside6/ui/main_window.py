from pathlib import Path
import subprocess
import sys
import webbrowser
from datetime import datetime
import time
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ..backend import (
    BACKENDS,
    BACKEND_FEATURES,
    available_backends,
    ensure_backend_installed,
    is_backend_installed,
    get_gtts_languages,
    get_edge_voices,
    get_kokoro_voices,
)
from ..utils.create_base_filename import create_base_filename
from ..utils.open_folder import open_folder
from ..utils.preferences import load_preferences, save_preferences
from ..utils.timer import Timer
from .preferences import PreferencesDialog

OUTPUT_DIR = Path("outputs")
MAX_TEXT_LENGTH = 1000


class SynthesizeWorker(QtCore.QThread):

    finished = QtCore.Signal(object, object, float)


    def __init__(self, func, text: str, output: Path, kwargs: dict):
        super().__init__()
        self.func = func
        self.text = text
        self.output = output
        self.kwargs = kwargs

    def run(self):
        try:
            start = time.time()
            with Timer():
                result = self.func(self.text, self.output, **self.kwargs)
            elapsed = time.time() - start
            err = None
        except Exception as e:
            elapsed = 0.0
            err = e
            result = None
        self.finished.emit(result, err, elapsed)


class InstallWorker(QtCore.QThread):
    finished = QtCore.Signal(str, object)

    def __init__(self, backend: str):
        super().__init__()
        self.backend = backend

    def run(self):
        from ..backend import ensure_backend_installed

        try:
            ensure_backend_installed(self.backend)
            err = None
        except Exception as e:
            err = e
        self.finished.emit(self.backend, err)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.prefs = load_preferences()
        global OUTPUT_DIR
        OUTPUT_DIR = Path(self.prefs.get("output_dir", "outputs"))
        self.setWindowTitle("PySide6 TTS Launcher")
        self.resize(400, 200)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)

        # --- Model selection row ---
        model_row = QtWidgets.QHBoxLayout()
        self.backend_combo = QtWidgets.QComboBox()
        self.backend_combo.addItems(available_backends())
        self.backend_combo.currentTextChanged.connect(self.on_backend_changed)
        self.backend_combo.currentTextChanged.connect(self.update_synthesize_enabled)
        model_row.addWidget(self.backend_combo)

        self.install_button = QtWidgets.QPushButton("Install Backend")
        self.install_button.clicked.connect(self.on_install_backend)
        model_row.addWidget(self.install_button)
        main_layout.addLayout(model_row)

        # --- Optional selectors row ---
        opts_row = QtWidgets.QHBoxLayout()
        self.voice_combo = QtWidgets.QComboBox()
        self.voice_combo.setEnabled(False)
        opts_row.addWidget(self.voice_combo)

        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.setEnabled(False)
        opts_row.addWidget(self.lang_combo)

        self.rate_widget = QtWidgets.QWidget()
        rate_row = QtWidgets.QHBoxLayout(self.rate_widget)
        rate_label = QtWidgets.QLabel("Speech Rate:")
        self.rate_spin = QtWidgets.QSpinBox()
        self.rate_spin.setRange(50, 300)
        self.rate_spin.setValue(200)
        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.rate_spin)
        opts_row.addWidget(self.rate_widget)

        self.seed_widget = QtWidgets.QWidget()
        seed_row = QtWidgets.QHBoxLayout(self.seed_widget)
        seed_label = QtWidgets.QLabel("Seed (0=random):")
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(0)
        seed_row.addWidget(seed_label)
        seed_row.addWidget(self.seed_spin)
        opts_row.addWidget(self.seed_widget)
        main_layout.addLayout(opts_row)

        # Text input area
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setPlaceholderText("Enter text to synthesize...")
        self.text_edit.textChanged.connect(self.update_synthesize_enabled)
        main_layout.addWidget(self.text_edit)

        self.audio_file: str | None = None
        self.load_audio_button = QtWidgets.QPushButton("Load Audio File")
        self.load_audio_button.clicked.connect(self.on_load_audio)
        self.load_audio_button.setVisible(False)
        main_layout.addWidget(self.load_audio_button)

        # Synthesize button
        self.button = QtWidgets.QPushButton("Synthesize")
        self.button.clicked.connect(self.on_synthesize)
        main_layout.addWidget(self.button)

        # --- Mini player row ---
        player_row = QtWidgets.QHBoxLayout()
        self.play_button = QtWidgets.QPushButton("Play")
        self.play_button.clicked.connect(self.on_play_output)
        self.play_button.setEnabled(False)
        player_row.addWidget(self.play_button)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop_playback)
        self.stop_button.setEnabled(False)
        player_row.addWidget(self.stop_button)

        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        player_row.addWidget(self.position_slider)
        main_layout.addLayout(player_row)

        # Autoplay option
        self.autoplay_check = QtWidgets.QCheckBox("Auto play after synthesis")
        self.autoplay_check.setChecked(self.prefs.get("autoplay", True))
        main_layout.addWidget(self.autoplay_check)

        # --- Misc buttons row ---
        misc_row = QtWidgets.QHBoxLayout()
        self.api_button = QtWidgets.QPushButton("Run API Server")
        self.api_button.clicked.connect(self.on_api_server_toggle)
        misc_row.addWidget(self.api_button)

        self.open_api_button = QtWidgets.QPushButton("Open API Docs")
        self.open_api_button.clicked.connect(self.on_open_api)
        misc_row.addWidget(self.open_api_button)

        self.open_button = QtWidgets.QPushButton("Open Output Folder")
        self.open_button.clicked.connect(self.on_open_output)
        misc_row.addWidget(self.open_button)

        self.pref_button = QtWidgets.QPushButton("Preferences")
        self.pref_button.clicked.connect(self.on_preferences)
        misc_row.addWidget(self.pref_button)
        main_layout.addLayout(misc_row)

        # History list
        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemActivated.connect(self.on_history_play)
        main_layout.addWidget(self.history_list)

        cb_form = QtWidgets.QFormLayout()
        self.cb_exaggeration = QtWidgets.QDoubleSpinBox()
        self.cb_exaggeration.setRange(0.25, 2.0)
        self.cb_exaggeration.setSingleStep(0.05)
        self.cb_exaggeration.setValue(0.5)
        cb_form.addRow("Exaggeration", self.cb_exaggeration)

        self.cb_cfg = QtWidgets.QDoubleSpinBox()
        self.cb_cfg.setRange(0.2, 1.0)
        self.cb_cfg.setSingleStep(0.05)
        self.cb_cfg.setValue(0.5)
        cb_form.addRow("CFG/Pace", self.cb_cfg)

        self.cb_temp = QtWidgets.QDoubleSpinBox()
        self.cb_temp.setRange(0.05, 5.0)
        self.cb_temp.setSingleStep(0.05)
        self.cb_temp.setValue(0.8)
        cb_form.addRow("Temperature", self.cb_temp)

        self.cb_voice_button = QtWidgets.QPushButton("Load Voice Prompt")
        self.cb_voice_button.clicked.connect(self.on_load_voice_prompt)
        cb_form.addRow(self.cb_voice_button)

        self.chatterbox_opts = QtWidgets.QGroupBox("Chatterbox Options")
        self.chatterbox_opts.setLayout(cb_form)
        self.chatterbox_opts.setVisible(False)
        main_layout.addWidget(self.chatterbox_opts)


        self.api_process = None
        self.last_output: Path | None = None
        self._synth_busy = False

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        # Qt6 renamed the signal from stateChanged to playbackStateChanged
        self.player.playbackStateChanged.connect(self.on_player_state_changed)
        self.player.durationChanged.connect(self.position_slider.setMaximum)
        self.player.positionChanged.connect(self.position_slider.setValue)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        self.cb_voice_path: str | None = None

        # Status label
        self.status = QtWidgets.QLabel()
        main_layout.addWidget(self.status)

        # Load voices for initial backend
        self.on_backend_changed(self.backend_combo.currentText())
        self.update_install_status()
        self.update_synthesize_enabled()

    def on_synthesize(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status.setText("Please enter some text")
            self.update_synthesize_enabled()
            return

        if len(text) > MAX_TEXT_LENGTH:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Long Input",
                f"The text is {len(text)} characters long. Continue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                self.update_synthesize_enabled()
                return

        backend = self.backend_combo.currentText()
        if not is_backend_installed(backend):
            self.status.setText("Backend not installed. Click 'Install Backend' first.")
            self.update_synthesize_enabled()
            return

        if backend in {"demucs", "vocos"}:
            # These tools operate on audio files rather than text
            if not self.audio_file or not Path(self.audio_file).is_file():
                self.status.setText("Please load an audio file first")
                self.update_synthesize_enabled()
                return
            text = self.audio_file


        self._synth_busy = True
        self.update_synthesize_enabled()
        output = self._generate_output_path(text, backend)
        rate = self.rate_spin.value()
        voice_id = self.voice_combo.currentData()
        lang_code = self.lang_combo.currentData()
        seed = self.seed_spin.value() or None

        func = BACKENDS[backend]
        features = BACKEND_FEATURES.get(backend, set())
        kwargs = {}
        if "rate" in features:
            if backend == "edge_tts":
                delta = rate - 200
                kwargs["rate"] = f"{delta:+d}%"
            else:
                kwargs["rate"] = rate
        if backend == "chatterbox":
            if self.cb_voice_path:
                kwargs["voice"] = self.cb_voice_path
            elif voice_id:
                kwargs["voice"] = voice_id
            kwargs["exaggeration"] = self.cb_exaggeration.value()
            kwargs["cfg_weight"] = self.cb_cfg.value()
            kwargs["temperature"] = self.cb_temp.value()
        elif "voice" in features and voice_id:
            kwargs["voice"] = voice_id
        if "lang" in features and lang_code:
            kwargs["lang"] = lang_code
        if "seed" in features and seed is not None:
            kwargs["seed"] = seed

        print(f"[INFO] Synthesizing with {backend}...")
        self.worker = SynthesizeWorker(func, text, output, kwargs)
        self.worker.finished.connect(self.on_synthesize_finished)
        self.worker.start()

    def on_api_server_toggle(self):
        self.api_button.setEnabled(False)
        if self.api_process is None:
            ensure_backend_installed("api_server")
            port = self.prefs.get("api_port", 8000)
            self.api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gui_pyside6.backend.api_server",
                    "--port",
                    str(port),
                ]
            )
            self.api_button.setText("Stop API Server")
            self.status.setText(f"API server started at http://127.0.0.1:{port}")
        else:
            self.api_process.terminate()
            self.api_process.wait()
            self.api_process = None
            self.api_button.setText("Run API Server")
            self.status.setText("API server stopped")
        QtCore.QTimer.singleShot(1000, lambda: self.api_button.setEnabled(True))

    def on_open_api(self):
        port = self.prefs.get("api_port", 8000)
        webbrowser.open(f"http://localhost:{port}/docs")

    def on_open_output(self):
        folder = self.last_output.parent if self.last_output else OUTPUT_DIR
        open_folder(str(folder))

    def on_play_output(self):
        if self.last_output and self.last_output.exists():
            self.player.setSource(QUrl.fromLocalFile(str(self.last_output)))
            self.player.play()
            self.stop_button.setEnabled(True)
        else:
            self.status.setText("No output file to play")

    def on_stop_playback(self):
        self.player.stop()

    def on_history_play(self, item: QtWidgets.QListWidgetItem):
        path = Path(item.text())
        if path.exists():
            self.last_output = path
            self.on_play_output()


    def on_synthesize_finished(self, result: object, error: object, elapsed: float):
        if error:
            self.status.setText(f"Error: {error}")
            print(f"[ERROR] {error}")
        else:
            output_desc = result
            if isinstance(result, list) and result:
                # demucs returns a list of stem paths
                output_desc = result[0].parent
                self.last_output = Path(result[0])
            elif isinstance(result, (str, Path)):
                self.last_output = Path(result)
            else:
                self.last_output = None

            print(f"[INFO] Output saved to {output_desc}")
            self.status.setText(f"Saved to {output_desc}")
            if self.last_output and self.last_output.exists():
                self.play_button.setEnabled(True)
            if isinstance(output_desc, Path):
                self.history_list.insertItem(0, str(output_desc))
            if self.history_list.count() > 10:
                self.history_list.takeItem(10)
            if self.autoplay_check.isChecked() and self.last_output:
                self.on_play_output()
        self._synth_busy = False
        self.update_synthesize_enabled()

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.stop_button.setEnabled(False)

    def on_load_audio(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Audio File", str(Path.home()), "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        )
        if file_path:
            self.audio_file = file_path
            self.load_audio_button.setText(Path(file_path).name)

            self.update_synthesize_enabled()

    def on_load_voice_prompt(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Voice Prompt", str(Path.home()), "Audio Files (*.wav);;All Files (*)"
        )
        if file_path:
            self.cb_voice_path = file_path
            self.cb_voice_button.setText(Path(file_path).name)

    def on_backend_changed(self, backend: str):
        self.update_install_status()
        features = BACKEND_FEATURES.get(backend, set())

        if not is_backend_installed(backend):
            self.voice_combo.clear()
            self.voice_combo.setEnabled(False)
            self.lang_combo.clear()
            self.lang_combo.setEnabled(False)
            self.rate_widget.setVisible(False)
            self.seed_widget.setVisible(False)
            return

        # configure voice and language lists
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
                languages = get_gtts_languages()
                self.lang_combo.clear()
                for code, name in languages.items():
                    self.lang_combo.addItem(f"{name} ({code})", code)
                self.lang_combo.setEnabled(True)
            elif backend == "edge_tts":
                voices = get_edge_voices()
                self.voice_combo.clear()
                for v in voices:
                    self.voice_combo.addItem(v, v)
                self.voice_combo.setEnabled(True)
                self.lang_combo.clear()
                self.lang_combo.setEnabled(False)
            elif backend == "kokoro":
                voices = get_kokoro_voices()
                self.voice_combo.clear()
                for name, ident in voices:
                    self.voice_combo.addItem(name, ident)
                self.voice_combo.setEnabled(True)
                self.lang_combo.clear()
                self.lang_combo.setEnabled(False)
            elif backend == "chatterbox":
                from ..backend import get_chatterbox_voices
                voices = get_chatterbox_voices()
                self.voice_combo.clear()
                self.voice_combo.addItem("(none)", None)
                for name, path in voices:
                    self.voice_combo.addItem(name, path)
                self.voice_combo.setEnabled(True)
                self.lang_combo.clear()
                self.lang_combo.setEnabled(False)
                self.cb_voice_path = None
                self.cb_voice_button.setText("Load Voice Prompt")
            else:
                self.lang_combo.clear()
                self.lang_combo.setEnabled(False)

        # final visibility based on declared feature support
        self.voice_combo.setVisible("voice" in features)
        self.lang_combo.setVisible("lang" in features)
        self.rate_widget.setVisible("rate" in features)
        self.seed_widget.setVisible("seed" in features)

        file_based = "file" in features
        self.load_audio_button.setVisible(file_based)
        if not file_based:
            self.audio_file = None
            self.load_audio_button.setText("Load Audio File")

        self.chatterbox_opts.setVisible(backend == "chatterbox")
        self.update_synthesize_enabled()


    def _generate_output_path(self, text: str, backend: str) -> Path:
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snippet = text[:15]
        features = BACKEND_FEATURES.get(backend, set())
        if "file" in features and Path(text).exists():
            snippet = Path(text).stem[:15]
        base = create_base_filename(snippet, str(OUTPUT_DIR), backend, date)
        if backend == "demucs":
            return Path(base)
        ext = ".mp3" if backend == "gtts" else ".wav"
        return Path(base + ext)

    def on_install_backend(self):
        backend = self.backend_combo.currentText()
        self.install_button.setEnabled(False)
        self.status.setText(f"Installing {backend}...")
        self.install_worker = InstallWorker(backend)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()

    def on_install_finished(self, backend: str, error: object):
        if error:
            self.status.setText(f"Install error: {error}")
        else:
            import importlib
            importlib.invalidate_caches()
            self.status.setText(f"{backend} installed")
        self.update_install_status()
        self.on_backend_changed(backend)
        self.update_synthesize_enabled()

    def update_install_status(self):
        backend = self.backend_combo.currentText()
        if is_backend_installed(backend):
            self.install_button.setEnabled(False)
            self.install_button.setText("Backend Installed")
        else:
            self.install_button.setEnabled(True)
            self.install_button.setText("Install Backend")
        self.update_synthesize_enabled()

    def update_synthesize_enabled(self):
        backend = self.backend_combo.currentText()
        features = BACKEND_FEATURES.get(backend, set())
        text_present = bool(self.text_edit.toPlainText().strip())
        if "file" in features:
            text_present = self.audio_file is not None
        backend_ready = is_backend_installed(backend)
        busy = getattr(self, "_synth_busy", False)
        self.button.setEnabled(text_present and backend_ready and not busy)

    def on_preferences(self):
        dlg = PreferencesDialog(self.prefs, self)
        if dlg.exec():
            self.prefs.update(dlg.get_preferences())
            save_preferences(self.prefs)
            self.autoplay_check.setChecked(self.prefs.get("autoplay", True))
            global OUTPUT_DIR
            OUTPUT_DIR = Path(self.prefs.get("output_dir", "outputs"))
            self.update_install_status()

    def closeEvent(self, event):
        self.prefs["autoplay"] = self.autoplay_check.isChecked()
        self.prefs["output_dir"] = str(OUTPUT_DIR)
        save_preferences(self.prefs)
        if self.api_process is not None:
            self.api_process.terminate()
            self.api_process.wait()
        super().closeEvent(event)

