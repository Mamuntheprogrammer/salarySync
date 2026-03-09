from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QMessageBox, QTextEdit, QGroupBox, QCheckBox)
import os
from services.legacy_import_service import LegacyImportService

class LegacyImportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.table_map = {
            "Company": "companies",
            "Business Area": "business_areas",
            "Designation": "designations",
            "Designation Subcategory": "designation_subcategories",
            "Shift": "shifts",
            "Employee": "employees",
            "Attendance": "attendance",
            "Weekly Holidays": "weekly_holidays",
            "Leave Quotas": "leave_quotas",
            "Holiday Calendar": "holiday_calendar",
            "Short Leave": "short_leaves",
            "Bonus": "bonuses"
        }
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        layout.addWidget(QLabel("<h2>Data Import Module</h2>"))
        layout.addWidget(QLabel("Select tables, download the template (one file with multiple sheets), fill it, and upload."))
        
        # Table Selection
        table_group = QGroupBox("Select Tables to Import")
        table_layout = QVBoxLayout()
        
        # Create check boxes
        self.checkboxes = []
        # sort keys to maintain consistent order
        for i, label in enumerate(self.table_map.keys()):
            cb = QCheckBox(label)
            if i == 0: cb.setChecked(True)
            self.checkboxes.append(cb)
            table_layout.addWidget(cb)
            
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
        self.btn_cancel = QPushButton("Clear Selection")
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
        
    def get_selected_table_types(self):
        selected = []
        for cb in self.checkboxes:
            if cb.isChecked():
                selected.append(self.table_map.get(cb.text()))
        return selected
        
    def download_template(self):
        # User requested ALL sheets to be present in the template regardless of selection
        all_table_types = list(self.table_map.values())
        
        # Default to data folder if exists, else downloads
        default_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            
        default_path = os.path.join(default_dir, "Import_Template.xlsx")
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Template", default_path, "Excel Files (*.xlsx)")
        
        if path:
            try:
                LegacyImportService.generate_template(all_table_types, path)
                QMessageBox.information(self, "Success", f"Template saved to: {path}")
                # Open folder
                try:
                    os.startfile(os.path.dirname(path))
                except:
                    pass
            except Exception as e:
                # Get full traceback
                import traceback
                tb = traceback.format_exc()
                QMessageBox.critical(self, "Error", f"Failed to save template: {e}\n\n{tb}")

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
        for cb in self.checkboxes:
            cb.setChecked(False)
        
    def run_import(self):
        if not self.selected_file: return
        table_types = self.get_selected_table_types()
        
        if not table_types:
             QMessageBox.warning(self, "No Selection", "Please select tables to import.")
             return
        
        self.txt_log.append("Starting Import Process...")
        self.btn_import.setEnabled(False)
        self.btn_template.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.repaint() # Force UI update
        
        total_success = 0
        total_errors = 0
        
        try:
            for table_type in table_types:
                self.txt_log.append(f"\n--- Importing {table_type} ---")
                count, errors = LegacyImportService.import_table_data(self.selected_file, table_type)
                
                self.txt_log.append(f"Imported: {count}")
                if errors:
                    self.txt_log.append("Errors / Warnings:")
                    for e in errors:
                        self.txt_log.append(f"- {e}")
                    total_errors += len(errors)
                else:
                    self.txt_log.append("No errors.")
                total_success += count
            
            self.txt_log.append(f"\nTotal Import Finished.\nTotal Success: {total_success}\nTotal Errors: {total_errors}")
            QMessageBox.information(self, "Import Complete", f"Process finished.\nTotal Success: {total_success}\nTotal Errors: {total_errors}")
            
        except Exception as e:
            self.txt_log.append(f"Critical Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
        
        self.btn_import.setEnabled(True)
        self.btn_template.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.btn_cancel.setEnabled(True)
