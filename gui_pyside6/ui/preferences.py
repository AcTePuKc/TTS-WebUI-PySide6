from __future__ import annotations

from PySide6 import QtWidgets, QtCore

from ..backend import available_backends, is_backend_installed, uninstall_backend
from ..utils.preferences import load_preferences


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, prefs: dict | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.prefs = prefs or load_preferences()

        layout = QtWidgets.QVBoxLayout(self)

        self.autoplay_box = QtWidgets.QCheckBox("Auto play after synthesis")
        self.autoplay_box.setChecked(self.prefs.get("autoplay", True))
        layout.addWidget(self.autoplay_box)

        self.backend_list = QtWidgets.QListWidget()
        layout.addWidget(self.backend_list)
        self.refresh_backends()

        btn_row = QtWidgets.QHBoxLayout()
        self.uninstall_btn = QtWidgets.QPushButton("Uninstall Selected")
        self.uninstall_btn.clicked.connect(self.on_uninstall)
        btn_row.addWidget(self.uninstall_btn)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def refresh_backends(self) -> None:
        self.backend_list.clear()
        for name in available_backends():
            installed = is_backend_installed(name)
            item = QtWidgets.QListWidgetItem(f"{name} - {'Installed' if installed else 'Missing'}")
            item.setData(QtCore.Qt.UserRole, name)
            self.backend_list.addItem(item)
            item.setSelected(False)

    def on_uninstall(self) -> None:
        for item in self.backend_list.selectedItems():
            backend = item.data(QtCore.Qt.UserRole)
            uninstall_backend(backend)
        self.refresh_backends()

    def get_preferences(self) -> dict:
        return {"autoplay": self.autoplay_box.isChecked()}

