import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide a dummy pyttsx3 module so the backend can import
dummy = types.ModuleType("pyttsx3")
dummy.init = lambda: None
sys.modules.setdefault("pyttsx3", dummy)
# Provide a dummy gtts module for the gtts backend
gtts_dummy = types.ModuleType("gtts")
gtts_dummy.gTTS = lambda *a, **k: None
sys.modules.setdefault("gtts", gtts_dummy)

from gui_pyside6.backend import api_server
from fastapi.testclient import TestClient


def test_synthesize_route_exists():
    routes = [r.path for r in api_server.app.routes]
    assert "/synthesize" in routes


def test_request_model_fields():
    model = api_server.SynthesisRequest(text="hi")
    assert hasattr(model, "rate")
    assert hasattr(model, "voice")
    assert hasattr(model, "lang")


def test_separate_route_exists():
    routes = [r.path for r in api_server.app.routes]
    assert "/separate" in routes


def test_transcribe_route_exists():
    routes = [r.path for r in api_server.app.routes]
    assert "/transcribe" in routes


def test_transcription_request_fields():
    model = api_server.TranscriptionRequest(audio="audio.wav")
    assert hasattr(model, "backend")
    assert hasattr(model, "model")


def test_root_returns_200():
    client = TestClient(api_server.app)
    resp = client.get("/")
    assert resp.status_code == 200
