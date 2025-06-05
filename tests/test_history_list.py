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
qtcore_mod.QUrl = Dummy
qtcore_mod.Qt = types.SimpleNamespace(Horizontal=0, UserRole=0)

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
qtwidgets_mod.QListWidget = DummyListWidget
qtwidgets_mod.QListWidgetItem = Dummy
qtwidgets_mod.QPushButton = Dummy
qtwidgets_mod.QCheckBox = Dummy
qtwidgets_mod.QPlainTextEdit = Dummy
qtwidgets_mod.QComboBox = Dummy
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

pyside6 = types.ModuleType('PySide6')
pyside6.QtCore = qtcore_mod
pyside6.QtWidgets = qtwidgets_mod
pyside6.QtMultimedia = qtmultimedia
sys.modules.setdefault('PySide6', pyside6)
sys.modules.setdefault('PySide6.QtCore', qtcore_mod)
sys.modules.setdefault('PySide6.QtWidgets', qtwidgets_mod)
sys.modules.setdefault('PySide6.QtMultimedia', qtmultimedia)

import importlib
from gui_pyside6.utils import preferences as prefs

def test_history_list_populated(tmp_path):
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
