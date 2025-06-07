import os
from PySide6 import QtWidgets
from gui_pyside6.utils.install_utils import inject_hybrid_site_packages

inject_hybrid_site_packages()

from gui_pyside6.ui.main_window import MainWindow


def main():
    torch_missing = False
    try:
        import torch  # noqa: F401
    except Exception:
        if os.environ.get("UV_APP_DRY") != "1":
            torch_missing = True
    app = QtWidgets.QApplication([])
    window = MainWindow(torch_missing=torch_missing)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
