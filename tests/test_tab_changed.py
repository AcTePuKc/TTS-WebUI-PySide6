import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Minimal PySide6 stubs
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
qtcore_mod.Qt = types.SimpleNamespace(Horizontal=0, Vertical=1, UserRole=0, AlignCenter=0)

class DummyPushButton(Dummy):
    def __init__(self, text='', *a, **k):
        super().__init__(*a, **k)
        self.clicked = DummySignal()
        self.visible = True
        self._text = text
    def setVisible(self, v):
        self.visible = v
    def isVisible(self):
        return self.visible
    def setText(self, t):
        self._text = t
    def text(self):
        return self._text

class DummyComboBox:
    def __init__(self, *a, **k):
        self.currentTextChanged = DummySignal()
        self.items = []
        self.enabled = False
    def addItems(self, items):
        for it in items:
            self.addItem(it)
    def addItem(self, text, data=None):
        self.items.append(text)
        if len(self.items) == 1:
            self.current = text
    def clear(self):
        self.items.clear()
    def setEnabled(self, val):
        self.enabled = val
    def setVisible(self, v):
        pass
    def currentText(self):
        return getattr(self, 'current', self.items[0] if self.items else '')

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
qtwidgets_mod.QPushButton = DummyPushButton
qtwidgets_mod.QCheckBox = Dummy
qtwidgets_mod.QListWidget = Dummy
qtwidgets_mod.QPlainTextEdit = Dummy
qtwidgets_mod.QComboBox = DummyComboBox
qtwidgets_mod.QHBoxLayout = Dummy
qtwidgets_mod.QVBoxLayout = Dummy
qtwidgets_mod.QFormLayout = Dummy
qtwidgets_mod.QGroupBox = Dummy
qtwidgets_mod.QSlider = Dummy
qtwidgets_mod.QLabel = Dummy
qtwidgets_mod.QSpinBox = Dummy
qtwidgets_mod.QListWidgetItem = Dummy

qtmultimedia_mod = types.ModuleType('QtMultimedia')
qtmultimedia_mod.QAudioOutput = Dummy
qtmultimedia_mod.QMediaPlayer = Dummy

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
pyside6.QtMultimedia = qtmultimedia_mod
sys.modules['PySide6'] = pyside6
sys.modules['PySide6.QtCore'] = qtcore_mod
sys.modules['PySide6.QtWidgets'] = qtwidgets_mod
sys.modules['PySide6.QtGui'] = qtgui_mod
sys.modules['PySide6.QtMultimedia'] = qtmultimedia_mod

import importlib
from gui_pyside6.utils import preferences as prefs

def _setup_pyside6_stubs():
    saved = {m: sys.modules[m] for m in list(sys.modules) if m.startswith('PySide6')}
    for m in list(saved):
        sys.modules.pop(m)
    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtCore'] = qtcore_mod
    sys.modules['PySide6.QtWidgets'] = qtwidgets_mod
    sys.modules['PySide6.QtGui'] = qtgui_mod
    sys.modules['PySide6.QtMultimedia'] = qtmultimedia_mod
    return saved


def test_tab_changed_hides_install_button(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.tts_combo.currentText = lambda: 'pyttsx3'
    window.tools_combo.currentText = lambda: 'tool'
    window.exp_combo.currentText = lambda: 'exp'

    calls = []
    window.on_backend_changed = lambda backend: calls.append(backend)

    assert window.install_button.isVisible()
    window.on_tab_changed(3)
    assert window.backend_combo is None
    assert not window.install_button.isVisible()
    assert calls == []

    window.on_tab_changed(0)
    assert window.backend_combo is window.tts_combo
    assert window.install_button.isVisible()
    assert calls == ['pyttsx3']

    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)
