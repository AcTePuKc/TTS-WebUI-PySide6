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
edge_dummy = types.ModuleType("edge_tts")
edge_dummy.Communicate = lambda *a, **k: type("C", (), {"save": lambda self, p: None})()
async def dummy_list_voices():
    return [{"ShortName": "en-US-GuyNeural", "Locale": "en-US"}]
edge_dummy.list_voices = dummy_list_voices
sys.modules.setdefault("edge_tts", edge_dummy)

# Dummy Kokoro module for listing voices
kokoro_mod = types.ModuleType("extension_kokoro")
kokoro_choices = types.ModuleType("extension_kokoro.CHOICES")
kokoro_choices.CHOICES = {"Heart": "af_heart"}
sys.modules.setdefault("extension_kokoro", kokoro_mod)
sys.modules.setdefault("extension_kokoro.CHOICES", kokoro_choices)

# Dummy Chatterbox module
chatter_mod = types.ModuleType("chatterbox")
class DummyChatterboxTTS:
    sr = 24000
    @classmethod
    def from_pretrained(cls, device):
        return cls()
    def prepare_conditionals(self, wav, exaggeration=0.5):
        pass
    def generate(self, *a, **k):
        import torch
        yield torch.zeros(1, 10)
chatter_mod.ChatterboxTTS = DummyChatterboxTTS
sys.modules.setdefault("chatterbox", chatter_mod)

from gui_pyside6.backend import available_backends, available_transcribers, get_mms_languages


def test_gtts_backend_available():
    assert "gtts" in available_backends()


def test_bark_backend_available():
    assert "bark" in available_backends()


def test_tortoise_backend_available():
    assert "tortoise" in available_backends()


def test_edge_tts_backend_available():
    assert "edge_tts" in available_backends()


def test_get_edge_voices_returns_list():
    from gui_pyside6.backend import get_edge_voices
    voices = get_edge_voices()
    assert isinstance(voices, list)
    assert voices and isinstance(voices[0], str)


def test_kokoro_backend_available():
    assert "kokoro" in available_backends()


def test_get_kokoro_voices_returns_list():
    from gui_pyside6.backend import get_kokoro_voices
    voices = get_kokoro_voices()
    assert isinstance(voices, list)
    assert voices and isinstance(voices[0], tuple) and len(voices[0]) == 2


def test_chatterbox_backend_available():
    assert "chatterbox" in available_backends()


def test_get_chatterbox_voices_returns_list():
    from gui_pyside6.backend import get_chatterbox_voices
    voices = get_chatterbox_voices()
    assert isinstance(voices, list)


def test_demucs_backend_available():
    assert "demucs" in available_backends()


def test_mms_backend_available():
    assert "mms" in available_backends()


def test_vocos_backend_available():
    assert "vocos" in available_backends()


def test_get_mms_languages_returns_list():
    langs = get_mms_languages()
    assert isinstance(langs, list)
    assert langs, "Language list should not be empty"
    assert isinstance(langs[0], tuple) and len(langs[0]) == 2


def test_whisper_backend_available():
    assert "whisper" in available_transcribers()
