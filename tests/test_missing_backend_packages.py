import os
import sys
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.backend import missing_backend_packages


def test_git_requirement_parsing():
    checked = []
    def fake_find_spec(name):
        checked.append(name)
        return object()

    with mock.patch('importlib.util.find_spec', side_effect=fake_find_spec):
        missing = missing_backend_packages('bark')

    assert not missing
    assert 'extension_bark' in checked


def test_case_insensitive_module_name():
    def fake_find_spec(name):
        if name == 'gtts':
            return object()
        return None

    with mock.patch('importlib.util.find_spec', side_effect=fake_find_spec):
        missing = missing_backend_packages('gtts')

    assert missing == []

