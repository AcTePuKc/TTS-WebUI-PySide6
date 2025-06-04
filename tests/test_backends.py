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
# Dummy bark module so import works
bark_dummy = types.ModuleType("bark")
bark_dummy.SAMPLE_RATE = 24000
def dummy_generate_audio(text, history_prompt=None):
    import numpy as np
    return np.zeros(10, dtype=np.float32)
bark_generation = types.ModuleType("bark.generation")
bark_generation.generate_audio = dummy_generate_audio
bark_generation.preload_models = lambda: None
bark_dummy.generation = bark_generation
sys.modules.setdefault("bark", bark_dummy)
sys.modules.setdefault("bark.generation", bark_generation)

from gui_pyside6.backend import available_backends


def test_gtts_backend_available():
    assert "gtts" in available_backends()


def test_bark_backend_available():
    assert "bark" in available_backends()


def test_tortoise_backend_available():
    assert "tortoise" in available_backends()
