from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QCheckBox, QGroupBox, 
                             QScrollArea, QMessageBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt
from config import Config
from services.import_service import ImportService
from services.sync_service import SyncService
import os

class ImportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.selected_file = None
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        layout.addWidget(QLabel("<h2>Data Import</h2>"))
        layout.addWidget(QLabel("Import data from Excel (.xlsx)."))
        
        # 1. Template
        tpl_group = QGroupBox("1. Setup & Template")
        tpl_layout = QHBoxLayout()
        
        btn_tpl = QPushButton("Download Template")
        btn_tpl.setToolTip("Generates Excel template with 10 rows of sample data")
        btn_tpl.clicked.connect(self.download_template)
        
        tpl_layout.addWidget(btn_tpl)
        tpl_layout.addStretch()
        tpl_group.setLayout(tpl_layout)
        layout.addWidget(tpl_group)
        
        # 2. Select File
        sel_group = QGroupBox("2. Select File")
        sel_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file selected")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_file)
        
        btn_clear = QPushButton("X")
        btn_clear.setFixedWidth(30)
        btn_clear.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        btn_clear.clicked.connect(self.clear_file)
        
        sel_layout.addWidget(btn_browse)
        sel_layout.addWidget(btn_clear)
        sel_layout.addWidget(self.lbl_file)
        sel_group.setLayout(sel_layout)
        layout.addWidget(sel_group)
        
        # 3. Select Tables (Dynamic)
        self.tbl_group = QGroupBox("3. Select Tables to Import")
        self.tbl_layout = QVBoxLayout() # Checkboxes go here
        
        # Scroll area for checkboxes if many sheets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.chk_container = QWidget()
        self.chk_layout = QVBoxLayout(self.chk_container)
        self.chk_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.chk_container)
        
        layout.addWidget(self.tbl_group)
        # We add validation to show this group only when file loaded? 
        # But we need layout space. Let's add scroll to tbl_group layout
        self.tbl_layout.addWidget(scroll)
        self.tbl_group.setLayout(self.tbl_layout)
        
        self.checkboxes = {}
        
        # 4. Import Action
        act_layout = QHBoxLayout()
        self.btn_import = QPushButton("Import Data")
        self.btn_import.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.run_import)
        act_layout.addWidget(self.btn_import)
        layout.addLayout(act_layout)
        
        # Log
        layout.addWidget(QLabel("Import Log:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
        layout.addWidget(self.txt_log)
        
    def download_template(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Template", "attensync_template.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                ImportService.generate_template(path)
                QMessageBox.information(self, "Success", "Template saved successfully.\nIt contains 10 rows of sample data for each table.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                
    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Import File", "", "Excel Files (*.xlsx)")
        if path:
            self.selected_file = path
            self.lbl_file.setText(path)
            self.parse_sheets()
            
    def clear_file(self):
        self.selected_file = None
        self.lbl_file.setText("No file selected")
        # Clear checkboxes
        for i in reversed(range(self.chk_layout.count())): 
            self.chk_layout.itemAt(i).widget().setParent(None)
        self.checkboxes = {}
        self.btn_import.setEnabled(False)
        self.txt_log.append("Selection cleared.")
            
    def parse_sheets(self):
        # Clear existing
        for i in reversed(range(self.chk_layout.count())): 
            self.chk_layout.itemAt(i).widget().setParent(None)
        self.checkboxes = {}
        
        try:
            sheets = ImportService.get_sheet_names(self.selected_file)
            if not sheets:
                self.txt_log.append("Error: No sheets found or invalid file.")
                return
                
            for sheet in sheets:
                chk = QCheckBox(sheet)
                chk.setChecked(True)
                self.chk_layout.addWidget(chk)
                self.checkboxes[sheet] = chk
                
            self.btn_import.setEnabled(True)
            self.txt_log.append(f"Loaded {len(sheets)} sheets. Select tables to import.")
            
        except Exception as e:
            self.txt_log.append(f"Error parsing file: {e}")
            
    def run_import(self):
        if not self.selected_file: return
        
        selected = [name for name, chk in self.checkboxes.items() if chk.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select at least one table.")
            return
            
        self.txt_log.append("Starting Import...")
        try:
            count, errors = ImportService.import_data(self.selected_file, selected)
            
            self.txt_log.append(f"Import Complete. Processed {count} records.")
            if errors:
                self.txt_log.append("Errors:")
                for err in errors:
                    self.txt_log.append(f"- {err}")
            else:
                self.txt_log.append("No errors.")
                
            QMessageBox.information(self, "Import Complete", f"Successfully processed {count} records.")
            
            # Prompt for Remote Sync
            self.prompt_remote_sync()
            
        except Exception as e:
            self.txt_log.append(f"Critical Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
            
    def prompt_remote_sync(self):
        config = Config.load_config()
        remote_cfg = config.get("remote_db", {})
        
        if remote_cfg.get("enabled"):
            confirm = QMessageBox.question(self, "Remote Sync", 
                "Import completed. Do you want to sync these changes to the Remote Database?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.txt_log.append("Syncing to Remote DB...")
                service = SyncService()
                success, msg = service.push_to_remote_db(remote_cfg["connection_string"], reset=False) # Update only?
                # Actually our push is smart enough? push_to_remote_db does copy_table.
                # If we use reset=False, it might duplicate if no primary keys match or error.
                # The current push implementation with reset=False does... nothing?
                # Let's check sync_service.py...
                # Ah, existing implementation of push_to_remote_db logic for reset=False was "pass" in the copy_table reset block, 
                # but then it proceeds to iterate local and insert.
                # BUT "upsert" logic relies on session.query(model).get(id).
                # So it WILL update existing records if IDs match.
                
                if success:
                    self.txt_log.append("Remote Sync Successful.")
                    QMessageBox.information(self, "Success", "Remote Sync Successful.")
                else:
                    self.txt_log.append(f"Remote Sync Failed: {msg}")
                    QMessageBox.warning(self, "Warning", f"Remote Sync Failed: {msg}")
