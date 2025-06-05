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
        return lambda *a, **k: None
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

qtwidgets = types.ModuleType('QtWidgets')
class DummyQtWidgetsModule(types.ModuleType):
    def __getattr__(self, name):
        return Dummy
qtwidgets_mod = DummyQtWidgetsModule('QtWidgets')

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

from gui_pyside6.ui.main_window import SynthesizeWorker


def dummy_backend(text, output, **kwargs):
    Path(output).write_text('done')


def test_synthesize_worker_prints_elapsed_time(capfd, tmp_path):
    out_path = tmp_path / 'out.txt'
    worker = SynthesizeWorker(dummy_backend, 'hi', out_path, {})
    worker.run()
    captured = capfd.readouterr().out
    assert 'Generated in' in captured and 'seconds' in captured
