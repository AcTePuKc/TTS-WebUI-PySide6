from __future__ import annotations

from PySide6 import QtWidgets, QtCore

from ..backend import available_backends, is_backend_installed, uninstall_backend
from ..utils.languages import get_available_languages
from ..utils.preferences import load_preferences
from ..utils.open_folder import open_log_dir


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, prefs: dict | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.prefs = prefs or load_preferences()

        layout = QtWidgets.QVBoxLayout(self)

        self.autoplay_box = QtWidgets.QCheckBox("Auto play after synthesis")
        self.autoplay_box.setChecked(self.prefs.get("autoplay", True))
        layout.addWidget(self.autoplay_box)

        port_row = QtWidgets.QHBoxLayout()
        port_label = QtWidgets.QLabel("API server port")
        self.port_spin = QtWidgets.QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.prefs.get("api_port", 8000))
        port_row.addWidget(port_label)
        port_row.addWidget(self.port_spin)
        layout.addLayout(port_row)

        out_row = QtWidgets.QHBoxLayout()
        out_label = QtWidgets.QLabel("Output directory")
        self.out_edit = QtWidgets.QLineEdit()
        self.out_edit.setText(self.prefs.get("output_dir", "outputs"))
        out_browse = QtWidgets.QPushButton("Browse")
        out_browse.clicked.connect(self.on_browse_output)
        out_row.addWidget(out_label)
        out_row.addWidget(self.out_edit)
        out_row.addWidget(out_browse)
        layout.addLayout(out_row)

        lang_row = QtWidgets.QHBoxLayout()
        lang_label = QtWidgets.QLabel("UI language")
        self.lang_combo = QtWidgets.QComboBox()
        self.languages = get_available_languages()
        for code, name in self.languages.items():
            self.lang_combo.addItem(name, code)
        pref_lang = self.prefs.get("ui_lang", "en")
        idx = self.lang_combo.findData(pref_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.lang_combo)
        layout.addLayout(lang_row)

        self.backend_list = QtWidgets.QListWidget()
        layout.addWidget(self.backend_list)
        self.refresh_backends()

        btn_row = QtWidgets.QHBoxLayout()
        self.uninstall_btn = QtWidgets.QPushButton("Uninstall Selected")
        self.uninstall_btn.clicked.connect(self.on_uninstall)
        btn_row.addWidget(self.uninstall_btn)
        log_btn = QtWidgets.QPushButton("Open Log File")
        log_btn.clicked.connect(self.on_open_log)
        btn_row.addWidget(log_btn)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def on_browse_output(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory", self.out_edit.text())
        if folder:
            self.out_edit.setText(folder)

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

    def on_open_log(self) -> None:
        open_log_dir()

    def get_preferences(self) -> dict:
        return {
            "autoplay": self.autoplay_box.isChecked(),
            "api_port": self.port_spin.value(),
            "output_dir": self.out_edit.text() or "outputs",
            "ui_lang": self.lang_combo.currentData() or "en",
        }

