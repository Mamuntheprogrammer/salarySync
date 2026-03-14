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
        layout.addWidget(QLabel("We will configure:\n- Database Location"))
        self.setLayout(layout)



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
