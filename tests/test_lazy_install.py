import os
import sys
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide a dummy pyttsx3 module so backend import works
dummy = type(sys)("pyttsx3")
dummy.init = lambda: None
sys.modules.setdefault("pyttsx3", dummy)
# Provide a dummy gtts module so backend import works
gtts_dummy = type(sys)("gtts")
gtts_dummy.gTTS = lambda *a, **k: None
sys.modules.setdefault("gtts", gtts_dummy)

from gui_pyside6.backend import ensure_backend_installed


def test_install_called_when_missing():
    with mock.patch('importlib.util.find_spec', return_value=None):
        with mock.patch('gui_pyside6.backend.install_package_in_venv') as install:
            ensure_backend_installed('pyttsx3')
            install.assert_called_once()


def test_install_skipped_when_present():
    with mock.patch('importlib.util.find_spec', return_value=object()):
        with mock.patch('gui_pyside6.backend.install_package_in_venv') as install:
            ensure_backend_installed('pyttsx3')
            install.assert_not_called()
