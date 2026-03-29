from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QLineEdit, QMessageBox,
                             QGroupBox, QFormLayout, QFileDialog)
from ui.btn_styles import btn_primary, btn_neutral
from ui.page_helpers import make_page_header
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Employee, PayrollRecord, BonusRecord
from utils.pdf_generator import PDFGenerator
import os


class PrintDocumentsModule(QWidget):
    def __init__(self, username="Admin"):
        super().__init__()
        self.username = username
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Print Documents",
                                          "Generate PDF payslips and bonus statements"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(16)
        cl.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_group = QGroupBox("Document Configuration")
        form = QFormLayout(config_group)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["Payslip", "Bonus Statement"])

        self.emp_code_input = QLineEdit()
        self.emp_code_input.setPlaceholderText("Enter Employee ID (numeric)")

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("YYYY  e.g. 2026")

        self.month_input = QLineEdit()
        self.month_input.setPlaceholderText("MM  e.g. 03")

        form.addRow("Document Type:", self.doc_type_combo)
        form.addRow("Employee ID:", self.emp_code_input)
        form.addRow("Year:", self.year_input)
        form.addRow("Month:", self.month_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_generate = QPushButton("🖨  Generate PDF")
        btn_generate.setStyleSheet(btn_primary())
        btn_generate.clicked.connect(self.generate_document)
        btn_row.addWidget(btn_generate)
        form.addRow(btn_row)

        cl.addWidget(config_group)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px; background: transparent;")
        cl.addWidget(self.lbl_status)
        cl.addStretch()

        layout.addWidget(content, stretch=1)

    def _set_status(self, msg, success=True):
        colour = "#388E3C" if success else "#D32F2F"
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f"color: {colour}; font-size: 13px; font-weight: 600; background: transparent;")

    def generate_document(self):
        emp_id_str = self.emp_code_input.text().strip()
        year_str = self.year_input.text().strip()
        month_str = self.month_input.text().strip()
        doc_type = self.doc_type_combo.currentText()

        if not emp_id_str or not year_str or not month_str:
            QMessageBox.warning(self, "Incomplete", "Please provide Employee ID, Year, and Month.")
            return

        try:
            year = int(year_str)
            month = int(month_str)
            emp_id = int(emp_id_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Employee ID, Year and Month must be valid numbers.")
            return

        session = get_db_session()
        emp = session.query(Employee).filter_by(id=emp_id).first()
        if not emp:
            QMessageBox.warning(self, "Not Found", f"Employee ID '{emp_id_str}' not found.")
            return

        if doc_type == "Payslip":
            record = session.query(PayrollRecord).filter_by(
                employee_id=emp.id, year=year, month=month
            ).first()
            if not record:
                QMessageBox.warning(self, "No Record",
                                    f"No payroll record for Employee {emp_id_str} in {year}-{month:02d}.\n"
                                    "Please run payroll first.")
                return
            default_fn = f"Payslip_{emp_id_str}_{year}_{month:02d}.pdf"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save Payslip", default_fn, "PDF Files (*.pdf)")
            if filepath:
                try:
                    PDFGenerator.generate_payslip(record, filepath, self.username)
                    self._set_status(f"✓ Payslip saved to: {filepath}")
                    if os.name == 'nt':
                        os.startfile(filepath)
                except Exception as e:
                    self._set_status(f"✗ Error: {e}", success=False)
                    QMessageBox.critical(self, "Error", str(e))

        elif doc_type == "Bonus Statement":
            record = session.query(BonusRecord).filter_by(
                employee_id=emp.id, year=year, month=month
            ).first()
            if not record:
                QMessageBox.warning(self, "No Record",
                                    f"No bonus record for Employee {emp_id_str} in {year}-{month:02d}.\n"
                                    "Please run bonus first.")
                return
            default_fn = f"Bonus_{emp_id_str}_{year}_{month:02d}.pdf"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save Bonus Statement", default_fn, "PDF Files (*.pdf)")
            if filepath:
                try:
                    PDFGenerator.generate_bonus_statement(record, filepath, self.username)
                    self._set_status(f"✓ Bonus statement saved to: {filepath}")
                    if os.name == 'nt':
                        os.startfile(filepath)
                except Exception as e:
                    self._set_status(f"✗ Error: {e}", success=False)
                    QMessageBox.critical(self, "Error", str(e))
