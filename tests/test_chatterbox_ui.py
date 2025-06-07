import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_on_install_finished import _setup_pyside6_stubs
from gui_pyside6.utils import preferences as prefs


def test_chatterbox_voice_dropdown_hidden(tmp_path):
    saved = _setup_pyside6_stubs()
    prefs.PREF_FILE = tmp_path / 'prefs.json'
    prefs.save_preferences({})

    import gui_pyside6.ui.main_window as main_window
    importlib.reload(main_window)

    main_window.is_backend_installed = lambda name: True
    import gui_pyside6.backend as backend_mod
    backend_mod.get_chatterbox_voices = lambda: []

    window = main_window.MainWindow()
    window.on_backend_changed('chatterbox')

    assert not getattr(window.voice_combo, 'visible', True)

    for m in list(sys.modules):
        if m.startswith('PySide6'):
            sys.modules.pop(m)
    sys.modules.update(saved)
