from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QMessageBox, QTextEdit, QGroupBox, QRadioButton, QButtonGroup)
import os
from services.legacy_import_service import LegacyImportService

class LegacyImportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.table_map = {
            "Employee": "employees",
            "Attendance": "attendance",
            "Shift": "shifts",
            "Designation": "designations",
            "Designation Subcategory": "designation_subcategories",
            "Company": "companies",
            "Business Area": "business_areas",
            "Weekly Holidays": "weekly_holidays",
            "Leave Quotas": "leave_quotas",
            "Holiday Calendar": "holiday_calendar"
        }
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        layout.addWidget(QLabel("<h2>Data Import Module</h2>"))
        layout.addWidget(QLabel("Select a table type, download the template, fill it, and upload."))
        
        # Table Selection
        table_group = QGroupBox("Select Table to Import")
        table_layout = QVBoxLayout()
        self.radio_group = QButtonGroup(self)
        
        # Create radio buttons
        self.radios = []
        for i, (label, key) in enumerate(self.table_map.items()):
            rb = QRadioButton(label)
            if i == 0: rb.setChecked(True) # Default first
            self.radio_group.addButton(rb)
            table_layout.addWidget(rb)
            self.radios.append(rb)
            
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Actions Row
        action_layout = QHBoxLayout()
        
        self.btn_template = QPushButton("Download Template")
        self.btn_template.clicked.connect(self.download_template)
        action_layout.addWidget(self.btn_template)
        
        self.btn_browse = QPushButton("Select File...")
        self.btn_browse.clicked.connect(self.browse_file)
        action_layout.addWidget(self.btn_browse)
        
        # Cancel Button (clears selection)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reset_state)
        action_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(action_layout)
        
        # File Display
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_file)
        
        # Import Button
        self.btn_import = QPushButton("Start Import")
        self.btn_import.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.run_import)
        layout.addWidget(self.btn_import)
        
        # Log
        layout.addWidget(QLabel("Import Log:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log)
        
    def get_selected_table_type(self):
        for rb in self.radios:
            if rb.isChecked():
                return self.table_map.get(rb.text())
        return None
        
    def download_template(self):
        table_type = self.get_selected_table_type()
        if not table_type: return
        
        # Default to data folder if exists, else downloads
        default_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            
        default_path = os.path.join(default_dir, f"{table_type}_Template.xlsx")
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Template", default_path, "Excel Files (*.xlsx)")
        if path:
            try:
                LegacyImportService.generate_template(table_type, path)
                QMessageBox.information(self, "Success", f"Template saved to: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template: {e}")

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx)")
        if path:
            self.selected_file = path
            self.lbl_file.setText(path)
            self.btn_import.setEnabled(True)
            self.txt_log.clear()
            self.txt_log.append(f"Selected file: {path}")
            
    def reset_state(self):
        self.selected_file = None
        self.lbl_file.setText("No file selected")
        self.btn_import.setEnabled(False)
        self.txt_log.clear()
        
    def run_import(self):
        if not self.selected_file: return
        table_type = self.get_selected_table_type()
        
        self.txt_log.append(f"Starting Import for {table_type}...")
        self.btn_import.setEnabled(False)
        self.btn_template.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.repaint() # Force UI update
        
        try:
            count, errors = LegacyImportService.import_table_data(self.selected_file, table_type)
            
            self.txt_log.append(f"\nImport Finished.\nSuccessfully Imported: {count}")
            if errors:
                self.txt_log.append("\nErrors / Warnings:")
                for e in errors:
                    self.txt_log.append(f"- {e}")
            else:
                self.txt_log.append("\nNo errors.")
                
            QMessageBox.information(self, "Import Complete", f"Import process finished.\nSuccess: {count}\nErrors: {len(errors)}")
            
        except Exception as e:
            self.txt_log.append(f"Critical Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
        
        self.btn_import.setEnabled(True)
        self.btn_template.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.btn_cancel.setEnabled(True)
