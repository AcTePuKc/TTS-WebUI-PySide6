import os
import sys
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.backend import _install_backend_packages


def _capture_calls():
    calls = []
    def _run(*a, **k):
        calls.append(('run', a[0]))
    def _call(cmd, **k):
        calls.append(('call', cmd))
    return calls, _run, _call


def test_uv_used_when_available():
    calls, run_fn, call_fn = _capture_calls()
    with mock.patch('gui_pyside6.backend._uv_available', return_value=True), \
         mock.patch('gui_pyside6.backend.install_utils._is_venv_active', return_value=True), \
         mock.patch('subprocess.run', side_effect=run_fn), \
         mock.patch('subprocess.check_call', side_effect=call_fn):
        _install_backend_packages(['foo'], no_deps=True)

    install_cmd = [c[1] for c in calls if c[0] == 'call'][0]
    assert install_cmd[:3] == ['uv', 'pip', 'install']
    assert '-p' in install_cmd
    assert '--no-deps' in install_cmd


def test_pip_used_when_uv_missing():
    calls, run_fn, call_fn = _capture_calls()
    with mock.patch('gui_pyside6.backend._uv_available', return_value=False), \
         mock.patch('gui_pyside6.backend.install_utils._is_venv_active', return_value=True), \
         mock.patch('subprocess.run', side_effect=run_fn), \
         mock.patch('subprocess.check_call', side_effect=call_fn):
        _install_backend_packages(['foo'], no_deps=False)

    install_cmd = [c[1] for c in calls if c[0] == 'call'][0]
    assert install_cmd[:4] == [sys.executable, '-m', 'pip', 'install']
    assert '--no-deps' not in install_cmd
