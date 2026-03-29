from ui.btn_styles import btn_primary, btn_neutral, btn_danger
from ui.page_helpers import make_page_header
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QLineEdit, QFileDialog,
                             QCheckBox, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from config import Config
from utils.backup_manager import BackupManager
from datetime import datetime


class BackupSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Backup & Restore",
                                          "Configure automatic backups and create manual snapshots"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(16)

        # Manual Backup
        manual_group = QGroupBox("Manual Backup")
        ml = QVBoxLayout(manual_group)
        ml.setSpacing(10)
        lbl = QLabel("Create an immediate snapshot of the database.")
        lbl.setStyleSheet("background: transparent;")
        ml.addWidget(lbl)
        btn_manual = QPushButton("⬇  Backup Database Now")
        btn_manual.setStyleSheet(btn_primary())
        btn_manual.clicked.connect(self.trigger_manual_backup)
        ml.addWidget(btn_manual)
        cl.addWidget(manual_group)

        # Auto Backup
        auto_group = QGroupBox("Auto Backup Configuration")
        al = QVBoxLayout(auto_group)
        al.setSpacing(10)

        self.chk_enable = QCheckBox("Enable automatic backup on application startup")
        al.addWidget(self.chk_enable)

        freq_row = QHBoxLayout()
        lbl_freq = QLabel("Frequency:")
        lbl_freq.setStyleSheet("background: transparent;")
        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["daily", "weekly"])
        self.combo_freq.setFixedWidth(140)
        freq_row.addWidget(lbl_freq)
        freq_row.addWidget(self.combo_freq)
        freq_row.addStretch()
        al.addLayout(freq_row)

        loc_row = QHBoxLayout()
        lbl_loc = QLabel("Backup Location:")
        lbl_loc.setStyleSheet("background: transparent;")
        self.txt_location = QLineEdit()
        self.txt_location.setReadOnly(True)
        self.txt_location.setPlaceholderText("Select a folder...")
        btn_browse = QPushButton("Browse...")
        btn_browse.setStyleSheet(btn_neutral())
        btn_browse.clicked.connect(self.browse_location)
        loc_row.addWidget(lbl_loc)
        loc_row.addWidget(self.txt_location)
        loc_row.addWidget(btn_browse)
        al.addLayout(loc_row)

        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(self.save_settings)
        al.addWidget(btn_save)

        cl.addWidget(auto_group)
        cl.addStretch()
        layout.addWidget(content, stretch=1)

    def load_settings(self):
        config = Config.load_config()
        backup_cfg = config.get("backup", {})
        self.chk_enable.setChecked(backup_cfg.get("enabled", False))
        self.combo_freq.setCurrentText(backup_cfg.get("frequency", "daily"))
        self.txt_location.setText(backup_cfg.get("location", str(Config.BACKUP_DIR)))

    def browse_location(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if dir_path:
            self.txt_location.setText(dir_path)

    def save_settings(self):
        config = Config.load_config()
        backup_cfg = config.get("backup", {})
        backup_cfg["enabled"] = self.chk_enable.isChecked()
        backup_cfg["frequency"] = self.combo_freq.currentText()
        backup_cfg["location"] = self.txt_location.text()
        config["backup"] = backup_cfg
        if Config.save_config(config):
            QMessageBox.information(self, "Success", "Backup settings saved successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings.")

    def trigger_manual_backup(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"attensync_manual_{timestamp}.db"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Backup", default_name, "SQLite DB (*.db)")
        if file_path:
            success, msg = BackupManager.perform_manual_backup(file_path)
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.critical(self, "Error", msg)
