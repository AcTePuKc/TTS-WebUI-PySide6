import os
import sys
import types
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import importlib
from gui_pyside6.utils import preferences as prefs


def _setup_pyside6_stubs():
    saved = {m: sys.modules[m] for m in list(sys.modules) if m.startswith('PySide6')}
    for m in list(saved):
        sys.modules.pop(m)

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
        pass

    qtcore_mod = types.ModuleType('QtCore')
    qtcore_mod.Signal = DummySignal
    qtcore_mod.QThread = DummyQThread
    class DummyQUrl:
        @staticmethod
        def fromLocalFile(p):
            return p
    qtcore_mod.QUrl = DummyQUrl
    qtcore_mod.Qt = types.SimpleNamespace(Horizontal=0, UserRole=0, AlignCenter=0)

    class DummyComboBox:
        def __init__(self, *a, **k):
            self.currentTextChanged = DummySignal()
            self.items = []
            self.enabled = False
            self.visible = True
        def addItems(self, items):
            for i in items:
                self.addItem(i)
        def addItem(self, text, data=None):
            self.items.append(text)
            if len(self.items) == 1:
                self.current = text
        def clear(self):
            self.items.clear()
        def setEnabled(self, val):
            self.enabled = val
        def setVisible(self, v):
            self.visible = v
        def currentText(self):
            if self.items:
                return getattr(self, 'current', self.items[0])
            return ''

    class DummyPlainTextEdit:
        def __init__(self, *a, **k):
            self.textChanged = DummySignal()
            self.text = ''
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
    qtwidgets_mod.QPushButton = Dummy
    qtwidgets_mod.QCheckBox = Dummy
    qtwidgets_mod.QListWidget = Dummy
    qtwidgets_mod.QPlainTextEdit = DummyPlainTextEdit
    qtwidgets_mod.QComboBox = DummyComboBox
    qtwidgets_mod.QHBoxLayout = Dummy
    qtwidgets_mod.QVBoxLayout = Dummy
    qtwidgets_mod.QFormLayout = Dummy
    qtwidgets_mod.QGroupBox = Dummy
    qtwidgets_mod.QSlider = Dummy
    qtwidgets_mod.QLabel = Dummy
    qtwidgets_mod.QSpinBox = Dummy
    qtwidgets_mod.QListWidgetItem = Dummy

    qtmultimedia = types.ModuleType('QtMultimedia')
    qtmultimedia.QAudioOutput = Dummy
    qtmultimedia.QMediaPlayer = Dummy

    qtgui_mod = types.ModuleType('QtGui')
    qtgui_mod.QImage = Dummy
    qtgui_mod.QPixmap = Dummy

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



def test_voices_available_after_install(tmp_path):
    saved = _setup_pyside6_stubs()

    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: name == 'edge_tts'
    main_window.get_edge_voices = lambda: ['Voice1', 'Voice2']

    window = main_window.MainWindow()
    assert window.voice_combo.items == []

    window.on_install_finished('edge_tts', None)

    assert window.voice_combo.items == ['Voice1', 'Voice2']

    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)
