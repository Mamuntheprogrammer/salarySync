from ui.btn_styles import btn_primary, btn_neutral, btn_danger
from ui.page_helpers import make_page_header
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QMessageBox, QTextEdit,
                             QGroupBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt
from services.legacy_import_service import LegacyImportService
import os


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
            "Bonus": "bonuses",
            "Salary Breakdown": "salary_breakdowns"
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Legacy Data Import",
                                          "Import existing data from Excel template into the database"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)

        # Table selection
        table_group = QGroupBox("Select Tables to Import")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(6)

        self.checkboxes = []
        for i, label in enumerate(self.table_map.keys()):
            cb = QCheckBox(label)
            if i == 0:
                cb.setChecked(True)
            self.checkboxes.append(cb)
            table_layout.addWidget(cb)
        cl.addWidget(table_group)

        # Action buttons row
        action_row = QHBoxLayout()
        self.btn_template = QPushButton("⬇  Download Template")
        self.btn_template.setStyleSheet(btn_neutral())
        self.btn_template.clicked.connect(self.download_template)

        self.btn_browse = QPushButton("📂  Select File...")
        self.btn_browse.setStyleSheet(btn_neutral())
        self.btn_browse.clicked.connect(self.browse_file)

        self.btn_cancel = QPushButton("✕  Clear Selection")
        self.btn_cancel.setStyleSheet(btn_danger())
        self.btn_cancel.clicked.connect(self.reset_state)

        action_row.addWidget(self.btn_template)
        action_row.addWidget(self.btn_browse)
        action_row.addWidget(self.btn_cancel)
        action_row.addStretch()
        cl.addLayout(action_row)

        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("color: #555; font-style: italic; background: transparent;")
        cl.addWidget(self.lbl_file)

        import_row = QHBoxLayout()
        import_row.addStretch()
        self.btn_import = QPushButton("⬆  Start Import")
        self.btn_import.setStyleSheet(btn_primary())
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.run_import)
        import_row.addWidget(self.btn_import)
        cl.addLayout(import_row)

        lbl_log = QLabel("Import Log:")
        lbl_log.setStyleSheet("font-weight: 600; background: transparent;")
        cl.addWidget(lbl_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        cl.addWidget(self.txt_log)

        layout.addWidget(content, stretch=1)

    def get_selected_table_types(self):
        return [self.table_map.get(cb.text()) for cb in self.checkboxes if cb.isChecked()]

    def download_template(self):
        all_table_types = list(self.table_map.values())
        default_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, "Import_Template.xlsx")
        path, _ = QFileDialog.getSaveFileName(self, "Save Template", default_path, "Excel Files (*.xlsx)")
        if path:
            try:
                LegacyImportService.generate_template(all_table_types, path)
                QMessageBox.information(self, "Success", f"Template saved to:\n{path}")
                try:
                    os.startfile(os.path.dirname(path))
                except Exception:
                    pass
            except Exception as e:
                import traceback
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{e}\n\n{traceback.format_exc()}")

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx)")
        if path:
            self.selected_file = path
            self.lbl_file.setText(path)
            self.btn_import.setEnabled(True)
            self.txt_log.clear()
            self.txt_log.append(f"Selected: {path}")

    def reset_state(self):
        self.selected_file = None
        self.lbl_file.setText("No file selected")
        self.btn_import.setEnabled(False)
        self.txt_log.clear()
        for cb in self.checkboxes:
            cb.setChecked(False)

    def run_import(self):
        if not self.selected_file:
            return
        table_types = self.get_selected_table_types()
        if not table_types:
            QMessageBox.warning(self, "No Selection", "Please select at least one table.")
            return

        for btn in [self.btn_import, self.btn_template, self.btn_browse, self.btn_cancel]:
            btn.setEnabled(False)

        self.txt_log.append("Starting Import Process...")
        self.repaint()

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
                        self.txt_log.append(f"  - {e}")
                    total_errors += len(errors)
                else:
                    self.txt_log.append("No errors.")
                total_success += count

            self.txt_log.append(
                f"\n✓ Import Finished  |  Success: {total_success}  |  Errors: {total_errors}"
            )
            QMessageBox.information(self, "Import Complete",
                                    f"Process finished.\nTotal Success: {total_success}\nTotal Errors: {total_errors}")
        except Exception as e:
            self.txt_log.append(f"Critical Error: {e}")
            QMessageBox.critical(self, "Error", str(e))

        for btn in [self.btn_import, self.btn_template, self.btn_browse, self.btn_cancel]:
            btn.setEnabled(True)
