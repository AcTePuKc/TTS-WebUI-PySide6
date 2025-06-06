import os, sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.utils.install_utils import (
    install_package_in_venv,
    uninstall_package_from_venv,
    inject_hybrid_site_packages,
)

def test_install_package_uses_ensurepip_and_pip():
    calls = []
    with mock.patch('subprocess.run') as run, mock.patch('subprocess.check_call') as call:
        run.side_effect = lambda *a, **k: calls.append(('run', a[0])) or None
        call.side_effect = lambda *a, **k: calls.append(('call', a[0])) or None
        install_package_in_venv('dummy')

    # first call should run ensurepip
    assert calls[0][0] == 'run'
    assert 'ensurepip' in calls[0][1]

    # there should be a pip install command at some point
    pip_calls = [c for c in calls if c[0] == 'call' and 'pip' in c[1]]
    assert pip_calls, "pip install was not called"


def test_active_env_detected_via_virtual_env_variable():
    calls = []
    with mock.patch.dict(os.environ, {"VIRTUAL_ENV": "/tmp/venv"}, clear=True):
        with mock.patch.object(sys, "prefix", sys.base_prefix), \
             mock.patch("subprocess.run") as run, \
             mock.patch("subprocess.check_call") as call:
            run.side_effect = lambda *a, **k: calls.append(('run', a[0])) or None
            call.side_effect = lambda *a, **k: calls.append(('call', a[0])) or None
            install_package_in_venv('dummy')

    python_used = [c for c in calls if c[0] == 'call' and 'pip' in c[1]][0][1][0]
    assert python_used == sys.executable


def test_active_env_detected_via_conda_prefix():
    calls = []
    with mock.patch.dict(os.environ, {"CONDA_PREFIX": "/tmp/conda"}, clear=True):
        with mock.patch.object(sys, "prefix", sys.base_prefix), \
             mock.patch("subprocess.run") as run, \
             mock.patch("subprocess.check_call") as call:
            run.side_effect = lambda *a, **k: calls.append(('run', a[0])) or None
            call.side_effect = lambda *a, **k: calls.append(('call', a[0])) or None
            install_package_in_venv('dummy')

    python_used = [c for c in calls if c[0] == 'call' and 'pip' in c[1]][0][1][0]
    assert python_used == sys.executable


def test_uninstall_package_uses_pip_uninstall():
    with mock.patch('gui_pyside6.utils.install_utils._is_venv_active', return_value=True), \
         mock.patch('subprocess.check_call') as call:
        uninstall_package_from_venv('dummy')
    call.assert_called_once()
    args = call.call_args[0][0]
    assert 'pip' in args and 'uninstall' in args


def test_inject_hybrid_site_packages_adds_path_when_no_env():
    with mock.patch('gui_pyside6.utils.install_utils._is_venv_active', return_value=False), \
         mock.patch('gui_pyside6.utils.install_utils._venv_site_packages', return_value=Path('/tmp/site')), \
         mock.patch('gui_pyside6.utils.install_utils._ensure_venv') as ensure:
        fake_path = []
        with mock.patch.object(sys, 'path', fake_path):
            inject_hybrid_site_packages()
        assert fake_path == ['/tmp/site']
        ensure.assert_called_once()


def test_inject_hybrid_site_packages_noop_when_env_active():
    with mock.patch('gui_pyside6.utils.install_utils._is_venv_active', return_value=True), \
         mock.patch('gui_pyside6.utils.install_utils._ensure_venv') as ensure:
        fake_path = []
        with mock.patch.object(sys, 'path', fake_path):
            inject_hybrid_site_packages()
        assert fake_path == []
        ensure.assert_not_called()
