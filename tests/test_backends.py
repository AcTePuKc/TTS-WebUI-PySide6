import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide dummy TTS modules so backend import works
import types
pyttsx3_dummy = types.ModuleType("pyttsx3")
pyttsx3_dummy.init = lambda: None
sys.modules.setdefault("pyttsx3", pyttsx3_dummy)
gtts_dummy = types.ModuleType("gtts")
gtts_dummy.gTTS = lambda *a, **k: None
sys.modules.setdefault("gtts", gtts_dummy)

from gui_pyside6.backend import available_backends


def test_gtts_backend_available():
    assert "gtts" in available_backends()
