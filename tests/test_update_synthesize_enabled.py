import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_history_list import _setup_pyside6_stubs, qtwidgets_mod
from gui_pyside6.utils import preferences as prefs


def test_stored_text_enables_synth(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import importlib
    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True

    window = main_window.MainWindow()

    window.synth_button._enabled = False
    window.synth_button.setEnabled = lambda val: setattr(window.synth_button, '_enabled', val)
    window.synth_button.isEnabled = lambda: getattr(window.synth_button, '_enabled', False)

    window.text_edit._stored_text = "hello"
    window.text_edit.toPlainText = lambda: ""

    window.update_synthesize_enabled()

    assert window.synth_button.isEnabled() is True

    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)
