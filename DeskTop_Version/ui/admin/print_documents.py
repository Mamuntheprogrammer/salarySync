from ui.custom_widgets import make_input_group
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QLineEdit, QMessageBox, QGroupBox, QFormLayout, QFileDialog)
from ui.btn_styles import btn_primary
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
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("<h2>Print Documents (Payslip / Bonus)</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        search_box = QGroupBox("Document configuration")
        form = QFormLayout()
        
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["Payslip", "Bonus Statement"])
        form.addRow(make_input_group("Document Type:", self.doc_type_combo))

        self.emp_code_input = QLineEdit()
        self.emp_code_input.setPlaceholderText("Enter Employee ID")
        form.addRow(make_input_group("Employee ID:", self.emp_code_input))
        
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("YYYY (e.g. 2026)")
        form.addRow(make_input_group("Year:", self.year_input))
        
        self.month_input = QLineEdit()
        self.month_input.setPlaceholderText("MM (e.g. 02)")
        form.addRow(make_input_group("Month:", self.month_input))
        
        btn_generate = QPushButton("Generate PDF")
        btn_generate.setStyleSheet(btn_primary())
        btn_generate.clicked.connect(self.generate_document)
        form.addRow(btn_generate)
        
        search_box.setLayout(form)
        layout.addWidget(search_box)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
    def generate_document(self):
        emp_id_str = self.emp_code_input.text().strip()
        year_str = self.year_input.text().strip()
        month_str = self.month_input.text().strip()
        doc_type = self.doc_type_combo.currentText()
        
        if not emp_id_str or not year_str or not month_str:
            QMessageBox.warning(self, "Invalid Input", "Please provide Employee ID, Year, and Month.")
            return
            
        try:
            year = int(year_str)
            month = int(month_str)
            emp_id = int(emp_id_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Employee ID, Year and Month must be valid numbers.")
            return
            
        session = get_db_session()
        
        # 1. Check Employee
        emp = session.query(Employee).filter_by(id=emp_id).first()
        if not emp:
            QMessageBox.warning(self, "Error", f"Employee with ID '{emp_id_str}' not found.")
            return
            
        # 2. Query Record based on Doc Type
        if doc_type == "Payslip":
            record = session.query(PayrollRecord).filter_by(
                employee_id=emp.id, year=year, month=month
            ).first()
            
            if not record:
                QMessageBox.warning(self, "Not Found", f"No Payroll Record found for Employee ID {emp_id_str} in {year}-{month:02d}. Ensure payroll has been run.")
                return
                
            default_filename = f"Payslip_{emp_id_str}_{year}_{month:02d}.pdf"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save Document", default_filename, "PDF Files (*.pdf)")
            
            if filepath:
                try:
                    success = PDFGenerator.generate_payslip(record, filepath, self.username)
                    if success:
                        self.lbl_status.setText(f"Success! Saved to {filepath}")
                        if os.name == 'nt':
                            os.startfile(filepath)  # Open automatically on Windows
                except Exception as e:
                    self.lbl_status.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{str(e)}")
                    
        elif doc_type == "Bonus Statement":
            record = session.query(BonusRecord).filter_by(
                employee_id=emp.id, year=year, month=month
            ).first()
            
            if not record:
                QMessageBox.warning(self, "Not Found", f"No Bonus Record found for Employee ID {emp_id_str} in {year}-{month:02d}. Ensure bonus has been run.")
                return
                
            default_filename = f"Bonus_{emp_id_str}_{year}_{month:02d}.pdf"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save Document", default_filename, "PDF Files (*.pdf)")
            
            if filepath:
                try:
                    success = PDFGenerator.generate_bonus_statement(record, filepath, self.username)
                    if success:
                        self.lbl_status.setText(f"Success! Saved to {filepath}")
                        if os.name == 'nt':
                            os.startfile(filepath)  # Open automatically on Windows
                except Exception as e:
                    self.lbl_status.setText(f"Error: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{str(e)}")
