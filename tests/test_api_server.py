import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide a dummy pyttsx3 module so the backend can import
dummy = types.ModuleType("pyttsx3")
dummy.init = lambda: None
sys.modules.setdefault("pyttsx3", dummy)

from gui_pyside6.backend import api_server


def test_synthesize_route_exists():
    routes = [r.path for r in api_server.app.routes]
    assert "/synthesize" in routes


def test_request_model_fields():
    model = api_server.SynthesisRequest(text="hi")
    assert hasattr(model, "rate")
    assert hasattr(model, "voice")
