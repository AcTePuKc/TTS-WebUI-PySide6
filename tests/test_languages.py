import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui_pyside6.utils import languages


def test_user_translation_directory(tmp_path):
    user_dir = tmp_path / "translations"
    user_dir.mkdir()
    meta = {"code": "fr", "language": "French"}
    (user_dir / "fr.json").write_text(json.dumps(meta), encoding="utf-8")
    orig_dir = languages._USER_LANG_DIR
    languages._USER_LANG_DIR = user_dir
    try:
        langs = languages.get_available_languages()
    finally:
        languages._USER_LANG_DIR = orig_dir
    assert langs.get("fr") == "French"
