from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QCheckBox, QGroupBox, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from config import Config
from services.sync_service import SyncService
from datetime import datetime

class CloudSetup(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("<h2>Online Mode & Remote Database</h2>"))
        layout.addWidget(QLabel("Configure a central database for multi-user access or backup."))
        
        # 1. Connection
        conn_group = QGroupBox("Remote Connection")
        form = QFormLayout()
        
        self.txt_remote_uri = QLineEdit()
        self.txt_remote_uri.setPlaceholderText("postgresql://user:pass@host:port/dbname")
        form.addRow("Connection String:", self.txt_remote_uri)
        
        btn_test = QPushButton("Test Connection")
        btn_test.clicked.connect(self.test_connection)
        form.addRow(btn_test)
        
        conn_group.setLayout(form)
        layout.addWidget(conn_group)
        
        # 2. Modes
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout()
        
        self.chk_online = QCheckBox("Enable Online Mode (Direct Connection)")
        self.chk_online.setToolTip("If enabled, the app will connect directly to the Remote DB. Requires restart.")
        mode_layout.addWidget(self.chk_online)
        
        lbl_info = QLabel("<i>Note: Enabling Online Mode allows multiple users to work on the same data in real-time. Uncheck to work offline (Local DB).</i>")
        lbl_info.setStyleSheet("color: #666;")
        mode_layout.addWidget(lbl_info)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 3. Actions
        act_group = QGroupBox("Data Management")
        act_layout = QVBoxLayout()
        
        hbox = QHBoxLayout()
        
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_settings)
        hbox.addWidget(btn_save)
        
        act_layout.addLayout(hbox)
        
        hbox2 = QHBoxLayout()
        
        # Push Local -> Remote
        btn_push = QPushButton("Push Local -> Remote")
        btn_push.setToolTip("Uploads current Local Data to Remote DB (Overwrite Remote)")
        btn_push.setStyleSheet("background-color: #E91E63; color: white;")
        btn_push.clicked.connect(self.push_data)
        hbox2.addWidget(btn_push)
        
        # Pull Remote -> Local (Backup)
        btn_backup = QPushButton("Backup Remote -> Local")
        btn_backup.setToolTip("Downloads Remote Data to Local DB (Overwrite Local)")
        btn_backup.setStyleSheet("background-color: #2196F3; color: white;")
        btn_backup.clicked.connect(self.pull_data)
        hbox2.addWidget(btn_backup)
        
        act_layout.addLayout(hbox2)
        act_group.setLayout(act_layout)
        layout.addWidget(act_group)
        
        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
    def load_settings(self):
        config = Config.load_config()
        self.chk_online.setChecked(config.get("online_mode", False))
        
        remote_cfg = config.get("remote_db", {})
        self.txt_remote_uri.setText(remote_cfg.get("connection_string", ""))
        
        last_backup = remote_cfg.get("last_backup")
        if last_backup:
            self.lbl_status.setText(f"Last Backup: {last_backup}")

    def save_settings(self):
        config = Config.load_config()
        config["online_mode"] = self.chk_online.isChecked()
        
        if "remote_db" not in config:
            config["remote_db"] = {}
            
        config["remote_db"]["connection_string"] = self.txt_remote_uri.text()
        
        if Config.save_config(config):
            self.lbl_status.setText("Settings Saved. Please restart if you changed modes.")
            QMessageBox.information(self, "Saved", "Settings saved successfully.\nIf you changed Online Mode, please restart the application.")
        else:
             QMessageBox.critical(self, "Error", "Failed to save settings")
             
    def test_connection(self):
        uri = self.txt_remote_uri.text()
        service = SyncService()
        success, msg = service.test_remote_connection(uri)
        if success:
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)
            
    def push_data(self):
        confirm = QMessageBox.question(self, "Confirm Push", 
            "This will OVERWRITE the Remote Database with your Local Data.\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.lbl_status.setText("Pushing to Remote...")
            # Ensure we save URI first
            self.save_settings()
            uri = self.txt_remote_uri.text()
            
            service = SyncService()
            # Reset=True to ensure clean slate on remote for full sync
            success, msg = service.push_to_remote_db(uri, reset=True)
            
            if success:
                 self.lbl_status.setText("Push Complete.")
                 QMessageBox.information(self, "Success", "Local data pushed to Remote DB.")
            else:
                 self.lbl_status.setText("Push Failed.")
                 QMessageBox.critical(self, "Error", msg)

    def pull_data(self):
        confirm = QMessageBox.question(self, "Confirm Backup", 
            "This will DOWNLOAD data from Remote and OVERWRITE your Local Database.\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if confirm == QMessageBox.StandardButton.Yes:
            self.lbl_status.setText("Downloading Backup...")
            # Ensure we save URI first
            self.save_settings()
            uri = self.txt_remote_uri.text()
            
            service = SyncService()
            success, msg = service.pull_from_remote_db(uri)
            
            if success:
                 self.lbl_status.setText(f"Backup Complete: {datetime.now().strftime('%I:%M:%S %p')}")
                 QMessageBox.information(self, "Success", "Remote data backed up to Local DB.")
            else:
                 self.lbl_status.setText("Backup Failed.")
                 QMessageBox.critical(self, "Error", msg)
