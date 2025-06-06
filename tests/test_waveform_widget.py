import os
import sys
import types
import numpy as np

matplotlib = types.ModuleType('matplotlib')

class DummyFig:
    def __init__(self):
        self.canvas = types.SimpleNamespace(get_width_height=lambda: (1, 1))
    def savefig(self, buff, format='raw'):
        buff.write(b'\x00' * 4)

pyplot = types.ModuleType('pyplot')
pyplot.figure = lambda *a, **k: DummyFig()
pyplot.style = types.SimpleNamespace(use=lambda *a, **k: None)
pyplot.plot = lambda *a, **k: None
pyplot.axis = lambda *a, **k: None
pyplot.close = lambda *a, **k: None
matplotlib.use = lambda *a, **k: None
matplotlib.figure = types.SimpleNamespace(Figure=DummyFig)
sys.modules.setdefault('matplotlib', matplotlib)
sys.modules.setdefault('matplotlib.figure', matplotlib.figure)
sys.modules.setdefault('matplotlib.pyplot', pyplot)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Dummy:
    def __init__(self, *a, **k):
        pass
    def __getattr__(self, name):
        return lambda *a, **k: None
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
qtcore_mod.Qt = types.SimpleNamespace(AlignCenter=0, Horizontal=0, UserRole=0)

class DummyLabel:
    def __init__(self, *a, **k):
        self.pixmap = None
    def setPixmap(self, p):
        self.pixmap = p
    def setScaledContents(self, *a, **k):
        pass
    def setAlignment(self, *a, **k):
        pass
    def clear(self):
        self.pixmap = None

qtwidgets_mod = types.ModuleType('QtWidgets')
qtwidgets_mod.QLabel = DummyLabel
qtwidgets_mod.QMainWindow = Dummy
qtwidgets_mod.QDialog = Dummy
qtwidgets_mod.QWidget = Dummy
class DummyQTabWidget:
    def __init__(self, *a, **k):
        self.currentChanged = DummySignal()
    def addTab(self, *a, **k):
        pass
qtwidgets_mod.QTabWidget = DummyQTabWidget
qtwidgets_mod.QSlider = Dummy
qtwidgets_mod.QPushButton = Dummy
qtwidgets_mod.QCheckBox = Dummy
qtwidgets_mod.QListWidget = Dummy
qtwidgets_mod.QPlainTextEdit = Dummy
qtwidgets_mod.QComboBox = Dummy
qtwidgets_mod.QHBoxLayout = Dummy
qtwidgets_mod.QVBoxLayout = Dummy
qtwidgets_mod.QFormLayout = Dummy
qtwidgets_mod.QGroupBox = Dummy
qtwidgets_mod.QSpinBox = Dummy
qtwidgets_mod.QListWidgetItem = Dummy

class DummyImage:
    Format_RGBA8888 = 0
    def __init__(self, *a, **k):
        pass

class DummyPixmap:
    @staticmethod
    def fromImage(img):
        return 'pixmap'

qtgui_mod = types.ModuleType('QtGui')
qtgui_mod.QImage = DummyImage
qtgui_mod.QPixmap = DummyPixmap

qtmultimedia_mod = types.ModuleType('QtMultimedia')
qtmultimedia_mod.QAudioOutput = Dummy
qtmultimedia_mod.QMediaPlayer = Dummy

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
import gui_pyside6.ui.main_window as main_window
importlib.reload(main_window)
from gui_pyside6.ui.main_window import WaveformWidget


def test_waveform_widget_sets_pixmap():
    w = WaveformWidget()
    data = np.zeros(100)
    w.set_audio_array(data)
    assert w.pixmap == 'pixmap'
