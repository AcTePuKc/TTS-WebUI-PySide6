import os
import sys
import types
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide minimal PySide6 stubs with a working QListWidget
class Dummy:
    def __init__(self, *a, **k):
        pass
    def __getattr__(self, name):
        if name == 'connect':
            return lambda *a, **k: None
        return Dummy()
    def __call__(self, *a, **k):
        return Dummy()

class DummySignal:
    def __init__(self, *a, **k):
        pass
    def connect(self, *a, **k):
        pass
    def emit(self, *a, **k):
        pass

class DummyQThread:
    def __init__(self, *a, **k):
        pass

qtcore_mod = types.ModuleType('QtCore')
qtcore_mod.Signal = DummySignal
qtcore_mod.QThread = DummyQThread
class DummyQUrl:
    @staticmethod
    def fromLocalFile(p):
        return p
qtcore_mod.QUrl = DummyQUrl
qtcore_mod.Qt = types.SimpleNamespace(Horizontal=0, Vertical=1, UserRole=0, AlignCenter=0)

class DummyListWidget:
    def __init__(self, *a, **k):
        self.items = []
        self.itemActivated = DummySignal()
    def insertItem(self, index, text):
        self.items.insert(index, text)
    def count(self):
        return len(self.items)
    def takeItem(self, index):
        if len(self.items) > index:
            self.items.pop(index)

class DummyQtWidgetsModule(types.ModuleType):
    def __getattr__(self, name):
        return Dummy

qtwidgets_mod = DummyQtWidgetsModule('QtWidgets')
qtwidgets_mod.QMainWindow = Dummy
qtwidgets_mod.QDialog = Dummy
qtwidgets_mod.QWidget = Dummy
class DummyQTabWidget:
    def __init__(self, *a, **k):
        self.currentChanged = DummySignal()
    def addTab(self, *a, **k):
        pass
qtwidgets_mod.QTabWidget = DummyQTabWidget
qtwidgets_mod.QListWidget = DummyListWidget
qtwidgets_mod.QListWidgetItem = Dummy
class DummyPushButton:
    def __init__(self, text="", *a, **k):
        self._text = text
        self.clicked = DummySignal()
        self.visible = True
    def setText(self, t):
        self._text = t
    def text(self):
        return self._text
    def setVisible(self, v):
        self.visible = v
    def isVisible(self):
        return self.visible
    def __getattr__(self, name):
        return lambda *a, **k: None

qtwidgets_mod.QPushButton = DummyPushButton
qtwidgets_mod.QCheckBox = Dummy

class DummyPlainTextEdit:
    def __init__(self, *a, **k):
        self.textChanged = DummySignal()
        self.text = ""
        self.visible = True
    def setPlaceholderText(self, *a, **k):
        pass
    def setPlainText(self, t):
        self.text = t
    def toPlainText(self):
        return self.text
    def setReadOnly(self, *a, **k):
        pass
    def setVisible(self, v):
        self.visible = v
    def isVisible(self):
        return self.visible

qtwidgets_mod.QPlainTextEdit = DummyPlainTextEdit
class DummyComboBox:
    def __init__(self, *a, **k):
        self.currentTextChanged = DummySignal()
    def addItems(self, *a, **k):
        pass
    def __getattr__(self, name):
        return lambda *a, **k: None
qtwidgets_mod.QComboBox = DummyComboBox
qtwidgets_mod.QHBoxLayout = Dummy
qtwidgets_mod.QVBoxLayout = Dummy
qtwidgets_mod.QFormLayout = Dummy
qtwidgets_mod.QGroupBox = Dummy
qtwidgets_mod.QSlider = Dummy
qtwidgets_mod.QLabel = Dummy
qtwidgets_mod.QSpinBox = Dummy

qtmultimedia = types.ModuleType('QtMultimedia')
qtmultimedia.QAudioOutput = Dummy
qtmultimedia.QMediaPlayer = Dummy

qtgui_mod = types.ModuleType('QtGui')
qtgui_mod.QImage = Dummy
class DummyPixmap:
    @staticmethod
    def fromImage(img):
        return 'pixmap'
qtgui_mod.QPixmap = DummyPixmap

pyside6 = types.ModuleType('PySide6')
pyside6.QtCore = qtcore_mod
pyside6.QtWidgets = qtwidgets_mod
pyside6.QtGui = qtgui_mod
pyside6.QtMultimedia = qtmultimedia
sys.modules['PySide6'] = pyside6
sys.modules['PySide6.QtCore'] = qtcore_mod
sys.modules['PySide6.QtWidgets'] = qtwidgets_mod
sys.modules['PySide6.QtGui'] = qtgui_mod
sys.modules['PySide6.QtMultimedia'] = qtmultimedia

import importlib
from gui_pyside6.utils import preferences as prefs


def _setup_pyside6_stubs():
    saved = {m: sys.modules[m] for m in list(sys.modules) if m.startswith('PySide6')}
    for m in list(saved):
        sys.modules.pop(m)

    pyside6 = types.ModuleType('PySide6')
    pyside6.QtCore = qtcore_mod
    pyside6.QtWidgets = qtwidgets_mod
    pyside6.QtGui = qtgui_mod
    pyside6.QtMultimedia = qtmultimedia
    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtCore'] = qtcore_mod
    sys.modules['PySide6.QtWidgets'] = qtwidgets_mod
    sys.modules['PySide6.QtGui'] = qtgui_mod
    sys.modules['PySide6.QtMultimedia'] = qtmultimedia
    return saved

def test_history_list_populated(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    # ensure backend considered installed
    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.autoplay_check = types.SimpleNamespace(isChecked=lambda: False)

    out_path = tmp_path / 'out.wav'
    out_path.write_text('x')

    window.on_synthesize_finished(out_path, None, 0.0)

    assert window.last_output == out_path
    assert window.history_list.items[0] == str(out_path)
    assert len(window.history_list.items) == 1
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_transcription_results_displayed(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.autoplay_check = types.SimpleNamespace(isChecked=lambda: False)

    window.on_synthesize_finished("hello world", None, 0.0)

    assert window.last_output is None
    assert window.transcript_view.toPlainText() == "hello world"
    assert window.transcript_view.isVisible()
    assert window.history_list.items[0].startswith("Transcribed:")
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_list_of_paths_handled(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.autoplay_check = types.SimpleNamespace(isChecked=lambda: False)

    # track waveform updates
    calls = []
    def fake_set_audio_file(self, path):
        calls.append(Path(path))
    window.waveform.set_audio_file = types.MethodType(fake_set_audio_file, window.waveform)

    p1 = tmp_path / 'seg1.wav'
    p2 = tmp_path / 'seg2.wav'
    p1.write_text('a')
    p2.write_text('b')

    window.on_synthesize_finished([p1, p2], None, 0.0)

    assert calls == [p2, p1, p1]

    assert window.last_output == p1
    assert window.history_list.items[0] == str(p1)
    assert window.history_list.items[1] == str(p2)
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_vocos_history_single_entry(tmp_path):
    """Vocos returns a single output path that should be added once."""
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.autoplay_check = types.SimpleNamespace(isChecked=lambda: False)

    vocos_out = tmp_path / 'vocos.wav'
    vocos_out.write_text('v')

    window.on_synthesize_finished(vocos_out, None, 0.0)

    assert window.last_output == vocos_out
    assert window.history_list.items[0] == str(vocos_out)
    assert len(window.history_list.items) == 1
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_whisper_does_not_leave_busy(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True
    main_window.TRANSCRIBERS['whisper'] = lambda audio, **kw: 'ok'

    class DummyWorker:
        def __init__(self, func, text, output, kwargs):
            self.func = func
            self.text = text
            self.output = output
            self.kwargs = kwargs
            self.finished = types.SimpleNamespace(connect=lambda cb: setattr(self, '_cb', cb))

        def start(self):
            if self.output is not None:
                result = self.func(self.text, self.output, **self.kwargs)
            else:
                result = self.func(self.text, **self.kwargs)
            if hasattr(self, '_cb'):
                self._cb(result, None, 0.0)

    main_window.SynthesizeWorker = DummyWorker

    window = main_window.MainWindow()
    window.autoplay_check = types.SimpleNamespace(isChecked=lambda: False)
    window.backend_combo.currentText = lambda: 'whisper'
    audio = tmp_path / 'in.wav'
    audio.write_text('dummy')
    window.audio_file = str(audio)

    window.on_synthesize()

    assert not window._synth_busy
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_button_visibility_updates_by_backend(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    assert window.synth_button.isVisible()
    assert not window.process_button.isVisible()
    assert not window.transcribe_button.isVisible()

    window.on_backend_changed('whisper')
    assert not window.synth_button.isVisible()
    # Whisper is a transcriber, not an audio tool
    assert not window.process_button.isVisible()
    assert window.transcribe_button.isVisible()

    window.on_backend_changed('pyttsx3')
    assert window.synth_button.isVisible()
    assert not window.process_button.isVisible()
    assert not window.transcribe_button.isVisible()
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)

