from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QLineEdit, QFileDialog, QCheckBox, 
                             QGroupBox, QMessageBox)
from config import Config
from utils.backup_manager import BackupManager
from datetime import datetime

class BackupSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("<h2>Backup Settings</h2>"))
        
        # 1. Manual Backup Section
        manual_group = QGroupBox("Manual Backup")
        manual_layout = QVBoxLayout()
        
        btn_manual = QPushButton("Backup Database Now")
        btn_manual.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        btn_manual.clicked.connect(self.trigger_manual_backup)
        manual_layout.addWidget(QLabel("Create an immediate copy of your database."))
        manual_layout.addWidget(btn_manual)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # 2. Auto Backup Section
        auto_group = QGroupBox("Auto Backup Configuration")
        auto_layout = QVBoxLayout()
        
        self.chk_enable = QCheckBox("Enable Auto-Backup on Startup")
        auto_layout.addWidget(self.chk_enable)
        
        # Frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency:"))
        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["daily", "weekly"])
        freq_layout.addWidget(self.combo_freq)
        freq_layout.addStretch()
        auto_layout.addLayout(freq_layout)
        
        # Location
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel("Backup Location:"))
        self.txt_location = QLineEdit()
        self.txt_location.setReadOnly(True)
        loc_layout.addWidget(self.txt_location)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_location)
        loc_layout.addWidget(btn_browse)
        
        auto_layout.addLayout(loc_layout)
        
        # Save Button
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_settings)
        auto_layout.addWidget(btn_save)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        layout.addStretch()
        
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
            QMessageBox.information(self, "Success", "Backup settings saved.")
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
