import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_history_list import _setup_pyside6_stubs, qtcore_mod, qtwidgets_mod, DummySignal, DummyPlainTextEdit
from gui_pyside6.utils import preferences as prefs


class DummyTimer:
    @staticmethod
    def singleShot(ms, func):
        func()


def _setup_with_signal():
    # Enable capturing of connected slots
    def connect(self, slot):
        self._slots = getattr(self, "_slots", [])
        self._slots.append(slot)

    def emit(self, *args, **kwargs):
        for s in getattr(self, "_slots", []):
            s(*args, **kwargs)

    DummySignal.connect = connect
    DummySignal.emit = emit

    # Provide document() API used by _record_text
    DummyPlainTextEdit.document = lambda self: types.SimpleNamespace(toPlainText=lambda: self.text)

    qtcore_mod.QTimer = DummyTimer
    return _setup_pyside6_stubs()


def test_text_changed_signal_updates_stored_and_enables(tmp_path):
    saved = _setup_with_signal()
    prefs.PREF_FILE = tmp_path / "prefs.json"
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()
    window.synth_button._enabled = False
    window.synth_button.setEnabled = lambda val: setattr(window.synth_button, "_enabled", val)
    window.synth_button.isEnabled = lambda: getattr(window.synth_button, "_enabled", False)

    window.text_edit.text = "hello"
    window.text_edit.textChanged.emit()

    assert window.text_edit._stored_text == "hello"
    assert window.synth_button.isEnabled() is True

    for m in list(sys.modules):
        if m.startswith("PySide6"):
            sys.modules.pop(m)
    sys.modules.update(saved)
