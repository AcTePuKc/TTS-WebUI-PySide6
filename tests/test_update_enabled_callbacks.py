import os
import sys
import types
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_history_list import _setup_pyside6_stubs, qtcore_mod, qtwidgets_mod
from gui_pyside6.utils import preferences as prefs


class DummyTimer:
    @staticmethod
    def singleShot(ms, func):
        func()


def _setup_with_timer():
    saved = _setup_pyside6_stubs()
    qtcore_mod.QTimer = DummyTimer
    return saved


def test_update_called_on_text_changed(tmp_path):
    saved = _setup_with_timer()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    calls = []
    window.update_synthesize_enabled = lambda: calls.append('call')

    window.on_text_changed()

    assert calls == ['call']
    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)


def test_update_called_on_load_audio(tmp_path):
    saved = _setup_with_timer()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True
    file_path = tmp_path / 'input.wav'
    file_path.write_text('x')
    qtwidgets_mod.QFileDialog = types.SimpleNamespace(
        getOpenFileName=lambda *a, **k: (str(file_path), '')
    )

    window = main_window.MainWindow()
    calls = []
    window.update_synthesize_enabled = lambda: calls.append('call')
    window.on_load_audio()
    assert calls == ['call']

    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)
