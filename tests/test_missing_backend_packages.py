import os
import sys
from unittest import mock
import importlib.metadata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.backend import missing_backend_packages


def test_git_requirement_parsing():
    checked = []

    def fake_distribution(name):
        checked.append(name)
        class D: ...
        return D()

    with mock.patch('importlib.metadata.distribution', side_effect=fake_distribution):
        missing = missing_backend_packages('bark')

    assert not missing
    assert 'bark' in checked


def test_case_insensitive_module_name():
    def fake_distribution(name):
        if name.lower() == 'gtts':
            class D: ...
            return D()
        raise importlib.metadata.PackageNotFoundError

    with mock.patch('importlib.metadata.distribution', side_effect=fake_distribution):
        missing = missing_backend_packages('gtts')

    assert missing == []


def test_kokoro_distribution_counts_as_installed():
    """``kokoro`` distribution should satisfy the ``kokoro`` backend."""

    def fake_distribution(name):
        if name == 'kokoro':
            class D: ...
            return D()
        raise importlib.metadata.PackageNotFoundError

    with mock.patch('importlib.metadata.distribution', side_effect=fake_distribution):
        missing = missing_backend_packages('kokoro')

    assert missing == []

