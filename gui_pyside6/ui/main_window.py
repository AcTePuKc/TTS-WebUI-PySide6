from pathlib import Path
import subprocess
import sys
import webbrowser
from datetime import datetime
import time
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ..backend import (
    BACKENDS,
    BACKEND_FEATURES,
    BACKEND_INFO,
    get_backend_repo,
    TTS_BACKENDS,
    TOOL_BACKENDS,
    EXPERIMENTAL_BACKENDS,
    TRANSCRIBERS,
    ensure_backend_installed,
    is_backend_installed,
    get_gtts_languages,
    get_edge_voices,
    get_kokoro_voices,
)
from ..utils.languages import find_qm_file
from ..utils.create_base_filename import create_base_filename
from ..utils.open_folder import open_folder
from ..utils.preferences import load_preferences, save_preferences
from ..utils.timer import Timer
from ..utils.waveform_plot import plot_waveform_as_image
from .preferences import PreferencesDialog

OUTPUT_DIR = Path("outputs")
MAX_TEXT_LENGTH = 1000


class SynthesizeWorker(QtCore.QThread):

    finished = QtCore.Signal(object, object, float)


    def __init__(self, func, text: str, output: Path | None, kwargs: dict):
        super().__init__()
        self.func = func
        self.text = text
        self.output = output
        self.kwargs = kwargs

    def run(self):
        try:
            start = time.time()
            with Timer():
                if self.output is not None:
                    result = self.func(self.text, self.output, **self.kwargs)
                else:
                    result = self.func(self.text, **self.kwargs)
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




LabelBase = QtWidgets.QLabel if isinstance(getattr(QtWidgets, "QLabel", object), type) else object


class WaveformWidget(LabelBase):
    """Simple widget to display an audio waveform."""

    seekRequested = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        if LabelBase is object:
            super().__init__()
        else:
            super().__init__(parent)
        if hasattr(self, "setAlignment"):
            self.setAlignment(QtCore.Qt.AlignCenter)
        if hasattr(self, "setScaledContents"):
            self.setScaledContents(True)
        self._pixmap_orig = None
        self._playback_ratio = 0.0
        self._duration_ms = 0

    def _update_scaled_pixmap(self):
        if self._pixmap_orig is None:
            return
        pixmap = self._pixmap_orig
        if hasattr(pixmap, "scaled"):
            pixmap = pixmap.scaled(
                self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
        self.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def set_duration(self, duration_ms: int):
        self._duration_ms = duration_ms

    def paintEvent(self, event):
        if LabelBase is not object:
            super().paintEvent(event)
            if self.pixmap() is None:
                return
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtGui.QColor("red"))
            pen.setWidth(2)
            painter.setPen(pen)
            x = int(self.width() * self._playback_ratio)
            painter.drawLine(x, 0, x, self.height())
        else:
            return

    def update_playback_position(self, position_ms: int, duration_ms: int):
        self._duration_ms = duration_ms
        if duration_ms > 0:
            ratio = max(0.0, min(1.0, position_ms / duration_ms))
        else:
            ratio = 0.0
        if ratio != self._playback_ratio:
            self._playback_ratio = ratio
            if hasattr(self, "update"):
                self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self._duration_ms > 0:
            pos = getattr(event, "position", lambda: None)()
            x = pos.x() if pos else event.x()
            ratio = x / max(1, self.width())
            position = int(ratio * self._duration_ms)
            self.seekRequested.emit(position)
            event.accept()
        super().mousePressEvent(event)

    def set_audio_array(self, audio_array):
        import numpy as np

        arr = np.asarray(audio_array)
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        img = plot_waveform_as_image(arr)
        h, w, _ = img.shape
        fmt = getattr(QtGui.QImage, "Format_RGBA8888", None)
        if fmt is not None:
            qimg = QtGui.QImage(img.data, w, h, fmt)
        else:
            qimg = QtGui.QImage()
        self._pixmap_orig = QtGui.QPixmap.fromImage(qimg)
        self._update_scaled_pixmap()

    def set_audio_file(self, path: str | Path):
        try:
            import soundfile as sf
            data, _ = sf.read(str(path))
        except Exception as e:
            print(f"[WARN] Failed to load waveform from {path}: {e}")
            self.clear()
            return
        self.set_audio_array(data)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.prefs = load_preferences()

        self._translator = None
        lang_code = self.prefs.get("ui_lang")
        if lang_code and lang_code != "en":
            qm_path = find_qm_file(lang_code)
            if qm_path:
                translator = QtCore.QTranslator()
                if translator.load(str(qm_path)):
                    QtCore.QCoreApplication.installTranslator(translator)
                    self._translator = translator
        self._current_lang = lang_code or "en"
        global OUTPUT_DIR
        OUTPUT_DIR = Path(self.prefs.get("output_dir", "outputs"))
        self.setWindowTitle("PySide6 TTS Launcher")
        self.resize(400, 200)

        if hasattr(QtWidgets, "QScrollArea"):
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            self.setCentralWidget(scroll)

            central = QtWidgets.QWidget()
            scroll.setWidget(central)
        else:
            central = QtWidgets.QWidget()
            self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)

        top_row = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_row)

        def safe_connect(signal, slot):
            try:
                signal.connect(slot)
            except Exception:
                pass

        # Status label created early so signal handlers can reference it
        self.status = QtWidgets.QLabel()

        params_group = QtWidgets.QGroupBox("Parameters")
        params_layout = QtWidgets.QVBoxLayout(params_group)
        top_row.addWidget(params_group, 3)

        # --- Backend selection tabs ---
        model_row = QtWidgets.QHBoxLayout()
        self.tabs = QtWidgets.QTabWidget()

        tts_tab = QtWidgets.QWidget()
        tts_layout = QtWidgets.QVBoxLayout(tts_tab)
        self.tts_combo = QtWidgets.QComboBox()
        self.tts_combo.addItems(TTS_BACKENDS)
        safe_connect(self.tts_combo.currentTextChanged, self.on_backend_changed)
        safe_connect(self.tts_combo.currentTextChanged, self.update_synthesize_enabled)
        tts_layout.addWidget(self.tts_combo)
        self.tabs.addTab(tts_tab, "TTS Engines")

        tools_tab = QtWidgets.QWidget()
        tools_layout = QtWidgets.QVBoxLayout(tools_tab)
        self.tools_combo = QtWidgets.QComboBox()
        self.tools_combo.addItems(TOOL_BACKENDS)
        safe_connect(self.tools_combo.currentTextChanged, self.on_backend_changed)
        safe_connect(self.tools_combo.currentTextChanged, self.update_synthesize_enabled)
        tools_layout.addWidget(self.tools_combo)
        self.tabs.addTab(tools_tab, "Audio Tools")

        exp_tab = QtWidgets.QWidget()
        exp_layout = QtWidgets.QVBoxLayout(exp_tab)
        self.exp_combo = QtWidgets.QComboBox()
        self.exp_combo.addItems(EXPERIMENTAL_BACKENDS)
        safe_connect(self.exp_combo.currentTextChanged, self.on_backend_changed)
        safe_connect(self.exp_combo.currentTextChanged, self.update_synthesize_enabled)
        exp_layout.addWidget(self.exp_combo)
        self.tabs.addTab(exp_tab, "Experimental")

        settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QVBoxLayout(settings_tab)
        self.pref_button = QtWidgets.QPushButton("Preferences")
        safe_connect(self.pref_button.clicked, self.on_preferences)
        settings_layout.addWidget(self.pref_button)
        self.tabs.addTab(settings_tab, "Settings")

        model_row.addWidget(self.tabs)


        self.install_button = QtWidgets.QPushButton("Install Backend")
        safe_connect(self.install_button.clicked, self.on_install_backend)
        model_row.addWidget(self.install_button)
        safe_connect(self.tabs.currentChanged, self.on_tab_changed)
        params_layout.addLayout(model_row)

        self.backend_combo = self.tts_combo

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
        params_layout.addLayout(opts_row)

        player_group = QtWidgets.QGroupBox("Player")
        player_layout = QtWidgets.QVBoxLayout(player_group)
        top_row.addWidget(player_group, 2)

        input_group = QtWidgets.QGroupBox("Input Text")
        input_layout = QtWidgets.QVBoxLayout(input_group)
        main_layout.addWidget(input_group)

        # Text input area
        self.text_edit = QtWidgets.QPlainTextEdit()
        _orig_set_plain = getattr(self.text_edit, "setPlainText", None)
        _orig_to_plain = getattr(self.text_edit, "toPlainText", None)
        self.text_edit._stored_text = ""

        def _set_plain(t):
            self.text_edit._stored_text = t
            if callable(_orig_set_plain):
                _orig_set_plain(t)

        def _to_plain():
            val = _orig_to_plain() if callable(_orig_to_plain) else None
            if val is None or val == "":
                return self.text_edit._stored_text
            return val

        def _record_text():
            val = _orig_to_plain() if callable(_orig_to_plain) else None
            if val is not None:
                self.text_edit._stored_text = str(val)

        self.text_edit.setPlainText = _set_plain
        self.text_edit.toPlainText = _to_plain
        self.text_edit.setPlaceholderText("Enter text to synthesize...")
        safe_connect(self.text_edit.textChanged, _record_text)
        safe_connect(self.text_edit.textChanged, self.on_text_changed)
        input_layout.addWidget(self.text_edit)

        self.audio_file: str | None = None
        self.load_audio_button = QtWidgets.QPushButton("Load Audio File")
        safe_connect(self.load_audio_button.clicked, self.on_load_audio)
        self.load_audio_button.setVisible(False)
        input_layout.addWidget(self.load_audio_button)

        # Display area for transcription results
        self.transcript_group = QtWidgets.QGroupBox("Transcription Output")
        transcript_layout = QtWidgets.QVBoxLayout(self.transcript_group)
        main_layout.addWidget(self.transcript_group)

        self.transcript_view = QtWidgets.QPlainTextEdit()
        _orig_set_plain = getattr(self.transcript_view, "setPlainText", None)
        _orig_to_plain = getattr(self.transcript_view, "toPlainText", None)
        _orig_set_vis = getattr(self.transcript_view, "setVisible", None)
        _orig_is_vis = getattr(self.transcript_view, "isVisible", None)
        self.transcript_view._stored_text = ""
        self.transcript_view._visible = False
        def _set_plain_t(t):
            self.transcript_view._stored_text = t
            if callable(_orig_set_plain):
                _orig_set_plain(t)
        def _to_plain_t():
            if callable(_orig_to_plain):
                val = _orig_to_plain()
                if val is not None:
                    return val
            return self.transcript_view._stored_text
        def _set_vis(v: bool):
            self.transcript_view._visible = v
            if callable(_orig_set_vis):
                _orig_set_vis(v)
            self.transcript_group.setVisible(v)
        def _is_vis():
            if callable(_orig_is_vis):
                val = _orig_is_vis()
                if val is not None:
                    return val
            return self.transcript_view._visible
        self.transcript_view.setPlainText = _set_plain_t
        self.transcript_view.toPlainText = _to_plain_t
        self.transcript_view.setVisible = _set_vis
        self.transcript_view.isVisible = _is_vis
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setPlaceholderText("Transcription output...")
        self.transcript_view.setVisible(False)
        transcript_layout.addWidget(self.transcript_view)
        self.transcript_group.setVisible(False)



        # --- Mini player row ---
        player_row = QtWidgets.QHBoxLayout()
        self.play_button = QtWidgets.QPushButton("Play")
        safe_connect(self.play_button.clicked, self.on_play_output)
        self.play_button.setEnabled(False)
        player_row.addWidget(self.play_button)

        self.stop_button = QtWidgets.QPushButton("Stop")
        safe_connect(self.stop_button.clicked, self.on_stop_playback)
        self.stop_button.setEnabled(False)
        player_row.addWidget(self.stop_button)

        self.duration_label = QtWidgets.QLabel("00:00 / 00:00")
        player_row.addWidget(self.duration_label)
        self.waveform = WaveformWidget()
        if hasattr(self.waveform, "setFixedWidth"):
            self.waveform.setFixedWidth(200)
        self.waveform._update_scaled_pixmap()
        player_row.addWidget(self.waveform)
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        if hasattr(self.volume_slider, "setFixedHeight"):
            self.volume_slider.setFixedHeight(80)
        volume_col = QtWidgets.QVBoxLayout()
        volume_col.addWidget(self.volume_slider)
        self.volume_label = QtWidgets.QLabel("100%")
        volume_col.addWidget(self.volume_label)
        player_row.addLayout(volume_col)
        player_layout.addLayout(player_row)

        # Autoplay option
        self.autoplay_check = QtWidgets.QCheckBox("Auto play after synthesis")
        self.autoplay_check.setChecked(self.prefs.get("autoplay", True))
        player_layout.addWidget(self.autoplay_check)

        buttons_row = QtWidgets.QHBoxLayout()
        self.button = QtWidgets.QPushButton("Synthesize")
        safe_connect(self.button.clicked, self.on_synthesize)
        buttons_row.addWidget(self.button)

        self.open_button = QtWidgets.QPushButton("Open Output Folder")
        safe_connect(self.open_button.clicked, self.on_open_output)
        buttons_row.addWidget(self.open_button)

        self.open_api_button = QtWidgets.QPushButton("Open API Docs")
        safe_connect(self.open_api_button.clicked, self.on_open_api)
        buttons_row.addWidget(self.open_api_button)

        self.api_button = QtWidgets.QPushButton("Run API Server")
        safe_connect(self.api_button.clicked, self.on_api_server_toggle)
        buttons_row.addWidget(self.api_button)
        input_layout.addLayout(buttons_row)

        history_group = QtWidgets.QGroupBox("History")
        history_layout = QtWidgets.QVBoxLayout(history_group)
        main_layout.addWidget(history_group)

        self.history_list = QtWidgets.QListWidget()
        supports_insert = True
        try:
            self.history_list.insertItem(0, "")
            supports_insert = self.history_list.count() > 0
            self.history_list.takeItem(0)
        except Exception:
            supports_insert = False

        if not supports_insert:
            if not isinstance(getattr(self.history_list, "items", None), list):
                self.history_list.items = []

            def _insert(idx, text, self=self.history_list):
                self.items.insert(idx, text)

            def _count(self=self.history_list):
                return len(self.items)

            def _take(idx, self=self.history_list):
                if len(self.items) > idx:
                    self.items.pop(idx)

            self.history_list.insertItem = _insert
            self.history_list.count = _count
            self.history_list.takeItem = _take
        safe_connect(self.history_list.itemActivated, self.on_history_play)
        history_layout.addWidget(self.history_list)

        cb_form = QtWidgets.QFormLayout()
        if hasattr(QtWidgets, "QDoubleSpinBox"):
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
        else:
            self.cb_exaggeration = self.cb_cfg = self.cb_temp = QtWidgets.QLabel()

        self.cb_voice_button = QtWidgets.QPushButton("Load Voice Prompt")
        safe_connect(self.cb_voice_button.clicked, self.on_load_voice_prompt)
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
        if hasattr(self.player, "setAudioOutput"):
            self.player.setAudioOutput(self.audio_output)
        # Qt6 renamed the signal from stateChanged to playbackStateChanged
        safe_connect(self.player.playbackStateChanged, self.on_player_state_changed)
        safe_connect(self.player.durationChanged, self.on_duration_changed)
        safe_connect(self.player.positionChanged, self.on_position_changed)
        safe_connect(self.waveform.seekRequested, self.player.setPosition)
        safe_connect(self.volume_slider.valueChanged, self.on_volume_changed)
        self.on_volume_changed(self.volume_slider.value())
        self.cb_voice_path: str | None = None

        # Status label placed at bottom of layout
        main_layout.addWidget(self.status)

        main_layout.setStretch(1, 1)
        main_layout.setStretch(3, 2)

        # Load voices for initial backend
        self.on_backend_changed(self.backend_combo.currentText())
        self._last_backend = self.backend_combo.currentText()
        self.update_synthesize_enabled()

    def on_synthesize(self):
        backend = self.backend_combo.currentText()
        features = BACKEND_FEATURES.get(backend, set())

        if not is_backend_installed(backend):
            if hasattr(self.status, "setText"):
                self.status.setText("Backend not installed. Click 'Install Backend' first.")
            self.update_synthesize_enabled()
            return

        if "file" in features:
            if not self.audio_file or not Path(self.audio_file).is_file():
                if hasattr(self.status, "setText"):
                    self.status.setText("Please load an audio file first")
                self.update_synthesize_enabled()
                return
            text = self.audio_file
        else:
            text = self.text_edit.toPlainText().strip()
            if not text:
                if hasattr(self.status, "setText"):
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


        output = self._generate_output_path(text, backend)
        if backend in TRANSCRIBERS:
            output = None
        rate = self.rate_spin.value()
        voice_id = self.voice_combo.currentData()
        lang_code = self.lang_combo.currentData()
        seed = self.seed_spin.value() or None

        lookup = TRANSCRIBERS if backend in TRANSCRIBERS else BACKENDS
        if backend not in lookup:
            if hasattr(self.status, "setText"):
                self.status.setText(f"Unknown backend: {backend}")
            self._synth_busy = False
            self.update_synthesize_enabled()
            return

        func = lookup[backend]
        self._synth_busy = True
        self.update_synthesize_enabled()
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
            if hasattr(self.cb_exaggeration, "value"):
                kwargs["exaggeration"] = self.cb_exaggeration.value()
            if hasattr(self.cb_cfg, "value"):
                kwargs["cfg_weight"] = self.cb_cfg.value()
            if hasattr(self.cb_temp, "value"):
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
            if hasattr(self.status, "setText"):
                self.status.setText(f"API server started at http://127.0.0.1:{port}")
        else:
            self.api_process.terminate()
            self.api_process.wait()
            self.api_process = None
            self.api_button.setText("Run API Server")
            if hasattr(self.status, "setText"):
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
            if hasattr(self.status, "setText"):
                self.status.setText("No output file to play")

    def on_stop_playback(self):
        self.player.stop()

    def on_history_play(self, item):
        path = Path(item.text())
        if path.exists():
            self.last_output = path
            self.on_play_output()


    def on_synthesize_finished(self, output: object, error: object, elapsed: float):
        if error:
            if hasattr(self.status, "setText"):
                self.status.setText(f"Error: {error}")
            print(f"[ERROR] {error}")
        else:
            self.transcript_view.setVisible(False)
            if isinstance(output, str) and not Path(output).exists():
                transcript = output
                self.transcript_view.setPlainText(transcript)
                self.transcript_view.setVisible(True)
                if hasattr(self.status, "setText"):
                    self.status.setText("Transcription complete")
                summary = transcript[:30].replace("\n", " ")
                self.history_list.insertItem(0, f"Transcribed: {summary}")
                output_desc = transcript
                self.last_output = None
            else:
                output_desc = output
                if isinstance(output, list) and output:
                    # demucs and future tools may return a list of file paths
                    if all(isinstance(p, (str, Path)) for p in output):
                        paths = [Path(p) for p in output]
                        first = paths[0]
                        output_desc = first.parent
                        self.last_output = first
                        for p in reversed(paths):
                            self.history_list.insertItem(0, str(p))
                    else:
                        self.last_output = None
                elif isinstance(output, (str, Path)):
                    p = Path(output)
                    self.last_output = p
                    output_desc = p
                    self.history_list.insertItem(0, str(p))
                else:
                    self.last_output = None

                print(f"[INFO] Output saved to {output_desc}")
                if hasattr(self.status, "setText"):
                    self.status.setText(f"Saved to {output_desc}")
                if self.last_output and self.last_output.exists():
                    self.play_button.setEnabled(True)
                if self.autoplay_check.isChecked() and self.last_output:
                    self.on_play_output()
                if self.last_output and self.last_output.exists():
                    self.waveform.set_audio_file(self.last_output)
                    self.player.setSource(QUrl.fromLocalFile(str(self.last_output)))
            count_fn = getattr(self.history_list, "count", None)
            take_fn = getattr(self.history_list, "takeItem", None)
            if callable(count_fn) and callable(take_fn):
                try:
                    if count_fn() > 10:
                        take_fn(10)
                except Exception:
                    pass
        self._synth_busy = False
        self.update_synthesize_enabled()

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.stop_button.setEnabled(False)

    def on_duration_changed(self, duration: int):
        self.waveform.set_duration(duration)
        self.update_position_label()

    def on_position_changed(self, position: int):
        self.update_position_label()
        self.waveform.update_playback_position(position, self.player.duration())

    def update_position_label(self):
        pos = self.player.position()
        dur = self.player.duration()
        self.duration_label.setText(f"{self._ms_to_mmss(pos)} / {self._ms_to_mmss(dur)}")

    def on_volume_changed(self, value: int):
        try:
            volume = max(0, min(100, int(value))) / 100
        except Exception:
            return
        self.audio_output.setVolume(volume)
        if hasattr(self.volume_label, "setText"):
            self.volume_label.setText(f"{int(volume*100)}%")

    @staticmethod
    def _ms_to_mmss(ms: int) -> str:
        seconds = int(ms / 1000)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def on_load_audio(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Audio File", str(Path.home()), "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        )
        if file_path:
            self.audio_file = file_path
            self.load_audio_button.setText(Path(file_path).name)

            self.waveform.set_audio_file(file_path)
            self.player.setSource(QUrl.fromLocalFile(file_path))

            self.update_synthesize_enabled()

    def on_load_voice_prompt(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Voice Prompt", str(Path.home()), "Audio Files (*.wav);;All Files (*)"
        )
        if file_path:
            self.cb_voice_path = file_path
            self.cb_voice_button.setText(Path(file_path).name)

    def on_tab_changed(self, index: int):
        if index == 0:
            self.backend_combo = self.tts_combo
        elif index == 1:
            self.backend_combo = self.tools_combo
        else:
            self.backend_combo = self.exp_combo
        self.on_backend_changed(self.backend_combo.currentText())

    def on_backend_changed(self, backend: str):
        prev_backend = getattr(self, "_last_backend", None)
        prev_features = BACKEND_FEATURES.get(prev_backend, set()) if prev_backend else set()
        if hasattr(self.button, "setText"):
            self.button.setText("Transcribe" if backend in TRANSCRIBERS else "Synthesize")
        if hasattr(self.status, "setText"):
            self.status.setText(BACKEND_INFO.get(backend, ""))
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

        import importlib
        importlib.invalidate_caches()

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
        self.text_edit.setVisible(not file_based)

        prev_file_based = "file" in prev_features
        if prev_file_based and not file_based:
            self.text_edit.setPlainText(self.text_edit._stored_text)
            self.update_synthesize_enabled()

        if not file_based:
            self.audio_file = None
            self.load_audio_button.setText("Load Audio File")
        parent = getattr(self.text_edit, "parentWidget", lambda: None)()
        layout = getattr(parent, "layout", lambda: None)()
        if layout is not None and hasattr(layout, "invalidate"):
            layout.invalidate()
        self.waveform._update_scaled_pixmap()

        self.chatterbox_opts.setVisible(backend == "chatterbox")
        self.update_synthesize_enabled()
        self._last_backend = backend


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
        repo = get_backend_repo(backend)
        if repo:
            self.status.setText(f"Installing {backend} from {repo}...")
        else:
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
        from ..backend import backend_was_installed
        if backend_was_installed(backend):
            self.install_button.setEnabled(False)
            self.install_button.setText("Backend Installed")
        else:
            self.install_button.setEnabled(True)
            self.install_button.setText("Install Backend")
        self.update_synthesize_enabled()

    def update_synthesize_enabled(self):
        backend = self.backend_combo.currentText()
        features = BACKEND_FEATURES.get(backend, set())
        file_required = "file" in features
        if file_required:
            text_present = bool(self.audio_file) and Path(self.audio_file).is_file()
        else:
            text = ""
            if hasattr(self.text_edit, "toPlainText"):
                val = self.text_edit.toPlainText()
                print(
                    f"[DEBUG] update_synthesize_enabled read text: {val}",
                    file=sys.__stdout__,
                )
                if val is not None:
                    text = str(val)
            text_present = bool(text.strip())
        backend_ready = is_backend_installed(backend)
        busy = getattr(self, "_synth_busy", False)
        print(
            f"[DEBUG] synth_btn state text_present={text_present}, backend_ready={backend_ready}, busy={busy}",
            file=sys.__stdout__,
        )
        self.button.setEnabled(text_present and backend_ready and not busy)

    def on_text_changed(self):
        print("[DEBUG] textChanged emitted", file=sys.__stdout__)
        self.update_synthesize_enabled()

    def on_preferences(self):
        dlg = PreferencesDialog(self.prefs, self)
        if dlg.exec():
            self.prefs.update(dlg.get_preferences())
            save_preferences(self.prefs)
            self.autoplay_check.setChecked(self.prefs.get("autoplay", True))
            global OUTPUT_DIR
            OUTPUT_DIR = Path(self.prefs.get("output_dir", "outputs"))
            self.update_install_status()

            new_lang = self.prefs.get("ui_lang", "en")
            if new_lang != self._current_lang:
                if self._translator:
                    QtCore.QCoreApplication.removeTranslator(self._translator)
                    self._translator = None
                if new_lang != "en":
                    qm_path = find_qm_file(new_lang)
                    if qm_path:
                        translator = QtCore.QTranslator()
                        if translator.load(str(qm_path)):
                            QtCore.QCoreApplication.installTranslator(translator)
                            self._translator = translator
                self._current_lang = new_lang

    def closeEvent(self, event):
        self.prefs["autoplay"] = self.autoplay_check.isChecked()
        self.prefs["output_dir"] = str(OUTPUT_DIR)
        self.prefs["ui_lang"] = self._current_lang
        save_preferences(self.prefs)
        if self.api_process is not None:
            self.api_process.terminate()
            self.api_process.wait()
        super().closeEvent(event)

