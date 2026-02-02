from PyQt6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QLabel, 
                             QLineEdit, QRadioButton, QButtonGroup, QFileDialog, QPushButton)
from config import Config
from database import db
import os 

class FirstRunWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AttenSync Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        self.addPage(WelcomePage())
        self.addPage(ConfigPage())
        self.addPage(DatabasePage())
        
        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self.on_finish)
        
    def on_finish(self):
        # Save configuration
        config_data = Config.load_config()
        
        # We would harvest data from pages here
        # For simplicity, we just save that setup is done
        config_data['setup_complete'] = True
        Config.save_config(config_data)
        self.accept()

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to AttenSync")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This wizard will guide you through the initial setup."))
        layout.addWidget(QLabel("We will configure:\n- Company Details\n- Database Location\n- Backup Settings"))
        self.setLayout(layout)

class ConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("General Configuration")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Time Format:"))
        self.btn_group = QButtonGroup()
        self.r1 = QRadioButton("12 Hour (AM/PM)")
        self.r2 = QRadioButton("24 Hour")
        self.r2.setChecked(True)
        self.btn_group.addButton(self.r1)
        self.btn_group.addButton(self.r2)
        layout.addWidget(self.r1)
        layout.addWidget(self.r2)
        
        self.setLayout(layout)
    
    def validatePage(self):
        config = Config.load_config()
        config['time_format'] = "12h" if self.r1.isChecked() else "24h"
        Config.save_config(config)
        return True

class DatabasePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Database Setup") 
        layout = QVBoxLayout()
        
        self.path_label = QLabel(Config.DEFAULT_CONFIG['db_path'])
        btn_browse = QPushButton("Choose Database Location")
        btn_browse.clicked.connect(self.choose_path)
        
        layout.addWidget(QLabel("Database File Path:"))
        layout.addWidget(self.path_label)
        layout.addWidget(btn_browse)
        self.setLayout(layout)
        
    def choose_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select Database File", "attensync.db")
        if path:
            self.path_label.setText(path)
            
    def validatePage(self):
        config = Config.load_config()
        config['db_path'] = self.path_label.text()
        Config.save_config(config)
        
        # Initialize DB at new location
        db.initialize()
        return True
