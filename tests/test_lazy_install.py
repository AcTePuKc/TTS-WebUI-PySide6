import os
import sys
import json
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

from gui_pyside6.backend import (
    ensure_backend_installed,
    is_backend_installed,
    uninstall_backend,
    backend_was_installed,
    load_persisted_installs,
)
import importlib.metadata


def test_install_called_when_missing():
    with mock.patch('importlib.metadata.distribution', side_effect=importlib.metadata.PackageNotFoundError):
        with mock.patch('gui_pyside6.backend.install_package_in_venv') as install:
            ensure_backend_installed('pyttsx3')
            install.assert_called_once()


def test_install_skipped_when_present():
    with mock.patch('importlib.metadata.distribution', return_value=object()):
        with mock.patch('gui_pyside6.backend.install_package_in_venv') as install:
            ensure_backend_installed('pyttsx3')
            install.assert_not_called()


def test_is_backend_installed_true():
    with mock.patch('importlib.metadata.distribution', return_value=object()):
        assert is_backend_installed('pyttsx3')


def test_is_backend_installed_false():
    with mock.patch('importlib.metadata.distribution', side_effect=importlib.metadata.PackageNotFoundError):
        assert not is_backend_installed('pyttsx3')


def test_kokoro_distribution_is_recognized():
    def fake_distribution(name):
        if name == 'kokoro':
            return object()
        raise importlib.metadata.PackageNotFoundError

    with mock.patch('importlib.metadata.distribution', side_effect=fake_distribution):
        assert is_backend_installed('kokoro')


def test_uninstall_backend_passes_distribution_names():
    with mock.patch('gui_pyside6.backend._get_backend_packages', return_value=['foo==1', 'bar @ git+https://x']):
        with mock.patch('gui_pyside6.backend.uninstall_package_from_venv') as uninstall:
            uninstall_backend('dummy')
            uninstall.assert_called_once_with(['foo', 'bar'])


def test_uninstall_skips_shared_dependencies(tmp_path):
    req_file = tmp_path / 'req.json'
    data = {
        'backend_a': ['foo==1', 'only_a==1'],
        'backend_b': ['foo==1']
    }
    req_file.write_text(json.dumps(data))

    with mock.patch('gui_pyside6.backend._REQ_FILE', req_file):
        with mock.patch('gui_pyside6.backend.is_backend_installed', side_effect=lambda n: n == 'backend_b'):
            with mock.patch('gui_pyside6.backend.uninstall_package_from_venv') as uninstall, \
                 mock.patch('gui_pyside6.backend._log_action') as log:
                uninstall_backend('backend_a')
                uninstall.assert_called_once_with(['only_a'])
                log.assert_any_call('skip_uninstall', 'backend_a', ['foo==1'])


def test_install_logged_and_persisted(tmp_path):
    log_dir = tmp_path
    log_file = log_dir / 'install.log'
    with mock.patch('gui_pyside6.backend._LOG_DIR', log_dir), \
         mock.patch('gui_pyside6.backend._INSTALL_LOG', log_file), \
         mock.patch('gui_pyside6.backend._get_backend_packages', return_value=['foo==1']), \
         mock.patch('importlib.metadata.distribution', side_effect=importlib.metadata.PackageNotFoundError), \
         mock.patch('gui_pyside6.backend.install_package_in_venv') as install:
        from gui_pyside6 import backend
        backend._INSTALLED_BACKENDS.clear()
        ensure_backend_installed('dummy')
        install.assert_called_once()
        assert log_file.exists()
        backend.load_persisted_installs()
        assert backend_was_installed('dummy')
