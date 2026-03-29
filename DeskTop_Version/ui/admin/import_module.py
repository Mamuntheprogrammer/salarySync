from ui.btn_styles import btn_primary, btn_neutral, btn_danger
from ui.page_helpers import make_page_header
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QCheckBox, QGroupBox,
                             QScrollArea, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt
from config import Config
from services.import_service import ImportService
from services.sync_service import SyncService
import os


class ImportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Data Import",
                                          "Import employees and attendance data from Excel (.xlsx)"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)

        # 1. Template
        tpl_group = QGroupBox("1. Setup & Template")
        tpl_layout = QHBoxLayout()
        
        btn_tpl = QPushButton("Download Template")
        btn_tpl.setStyleSheet(btn_neutral())
        btn_tpl.setToolTip("Generates Excel template with 10 rows of sample data")
        btn_tpl.clicked.connect(self.download_template)
        
        tpl_layout.addWidget(btn_tpl)
        tpl_layout.addStretch()
        tpl_group.setLayout(tpl_layout)
        cl.addWidget(tpl_group)

        # 2. Select File
        sel_group = QGroupBox("2. Select File")
        sel_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("background: transparent; color: #444;")
        btn_browse = QPushButton("Browse...")
        btn_browse.setStyleSheet(btn_neutral())
        btn_browse.clicked.connect(self.browse_file)

        btn_clear = QPushButton("✕ Clear")
        btn_clear.setStyleSheet(btn_danger())
        btn_clear.clicked.connect(self.clear_file)

        sel_layout.addWidget(btn_browse)
        sel_layout.addWidget(btn_clear)
        sel_layout.addWidget(self.lbl_file)
        sel_layout.addStretch()
        sel_group.setLayout(sel_layout)
        cl.addWidget(sel_group)

        # 3. Select Tables (Dynamic)
        self.tbl_group = QGroupBox("3. Select Tables to Import")
        self.tbl_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.chk_container = QWidget()
        self.chk_layout = QVBoxLayout(self.chk_container)
        self.chk_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.chk_container)
        self.tbl_layout.addWidget(scroll)
        self.tbl_group.setLayout(self.tbl_layout)
        cl.addWidget(self.tbl_group)

        self.checkboxes = {}

        # 4. Import Action
        act_row = QHBoxLayout()
        act_row.addStretch()
        self.btn_import = QPushButton("⬇  Import Selected Tables")
        self.btn_import.setStyleSheet(btn_primary())
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.run_import)
        act_row.addWidget(self.btn_import)
        cl.addLayout(act_row)

        # Log
        lbl_log = QLabel("Import Log:")
        lbl_log.setStyleSheet("background: transparent; font-weight: 600;")
        cl.addWidget(lbl_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(160)
        cl.addWidget(self.txt_log)

        layout.addWidget(content, stretch=1)
        
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
