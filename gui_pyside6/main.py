from PySide6 import QtWidgets
from gui_pyside6.utils.install_utils import inject_hybrid_site_packages

inject_hybrid_site_packages()

from gui_pyside6.ui.main_window import MainWindow


def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
