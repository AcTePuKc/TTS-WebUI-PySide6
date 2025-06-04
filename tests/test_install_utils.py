import os, sys
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.utils.install_utils import install_package_in_venv

def test_install_package_uses_ensurepip_and_pip():
    calls = []
    with mock.patch('subprocess.run') as run, mock.patch('subprocess.check_call') as call:
        run.side_effect = lambda *a, **k: calls.append(('run', a[0])) or None
        call.side_effect = lambda *a, **k: calls.append(('call', a[0])) or None
        install_package_in_venv('dummy')
    assert calls[0][0] == 'run'
    assert 'ensurepip' in calls[0][1]
    assert calls[1][0] == 'call'
    assert 'pip' in calls[1][1]
