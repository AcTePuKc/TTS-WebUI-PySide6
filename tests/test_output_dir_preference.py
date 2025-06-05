import os
import sys
import types
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide minimal PySide6 stubs
class Dummy:
    def __init__(self, *a, **k):
        pass
    def __getattr__(self, name):
        if name == 'connect':
            return lambda *a, **k: None
        return Dummy()
    def __call__(self, *a, **k):
        return Dummy()

qtcore = types.ModuleType('QtCore')
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
qtcore.Signal = DummySignal
qtcore.QThread = DummyQThread
qtcore.QUrl = Dummy
class DummyQtCoreModule(types.ModuleType):
    def __getattr__(self, name):
        return Dummy
qtcore_mod = DummyQtCoreModule('QtCore')
qtcore_mod.Signal = DummySignal
qtcore_mod.QThread = DummyQThread
qtcore_mod.QUrl = Dummy
qtcore_mod.Qt = types.SimpleNamespace(Horizontal=0, UserRole=0)

qtwidgets = types.ModuleType('QtWidgets')
class DummyQtWidgetsModule(types.ModuleType):
    def __getattr__(self, name):
        return Dummy()
qtwidgets_mod = DummyQtWidgetsModule('QtWidgets')
qtwidgets_mod.QMainWindow = Dummy
qtwidgets_mod.QDialog = Dummy

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


def test_output_dir_preference_used(tmp_path):
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    output_dir = tmp_path / 'custom_out'
    prefs.save_preferences({'output_dir': str(output_dir)})

    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    window = main_window.MainWindow()
    assert main_window.OUTPUT_DIR == output_dir
    path = window._generate_output_path('hello', 'pyttsx3')
    assert str(path).startswith(str(output_dir))
