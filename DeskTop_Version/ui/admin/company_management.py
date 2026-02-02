from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView)
from database import get_db_session
from models import Company, BusinessArea

class CompanyManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Company Management</h2>"))
        
        btn_add = QPushButton("Add Company")
        btn_add.clicked.connect(self.add_company_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Business Areas", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        companies = session.query(Company).all()
        
        self.table.setRowCount(0)
        for row, comp in enumerate(companies):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(comp.id)))
            self.table.setItem(row, 1, QTableWidgetItem(comp.code))
            self.table.setItem(row, 2, QTableWidgetItem(comp.name))
            
            ba_names = ", ".join([ba.name for ba in comp.business_areas])
            self.table.setItem(row, 3, QTableWidgetItem(ba_names))
            
            btn_manage = QPushButton("Manage Areas")
            btn_manage.clicked.connect(lambda checked, c=comp: self.manage_areas_dialog(c))
            self.table.setCellWidget(row, 4, btn_manage)
            
    def add_company_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Company")
        form = QFormLayout(dialog)
        
        code_input = QLineEdit()
        code_input.setMaxLength(4)
        code_input.setPlaceholderText("3 or 4 digit code")
        
        name_input = QLineEdit()
        
        form.addRow("Company Code:", code_input)
        form.addRow("Company Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_company(dialog, code_input.text(), name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_company(self, dialog, code, name):
        if len(code) < 3 or len(code) > 4:
            QMessageBox.warning(dialog, "Error", "Code must be 3 or 4 characters")
            return
            
        if not name:
            QMessageBox.warning(dialog, "Error", "Name is required")
            return
            
        session = get_db_session()
        try:
            if session.query(Company).filter_by(code=code).first():
                QMessageBox.warning(dialog, "Error", "Company Code already exists")
                return
                
            company = Company(code=code, name=name)
            session.add(company)
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def manage_areas_dialog(self, company):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Manage Business Areas - {company.name}")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        
        # Add Area Form
        form_layout = QHBoxLayout()
        
        code_input = QLineEdit()
        code_input.setMaxLength(2)
        code_input.setPlaceholderText("Code (2 digits)")
        code_input.setFixedWidth(100)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Area Name")
        
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(lambda: self.add_business_area(dialog, company.id, code_input.text(), name_input.text()))
        
        form_layout.addWidget(code_input)
        form_layout.addWidget(name_input)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)
        
        # List Existing Areas
        self.ba_table = QTableWidget()
        self.ba_table.setColumnCount(2)
        self.ba_table.setHorizontalHeaderLabels(["Code", "Name"])
        self.ba_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.ba_table)
        
        # Load Data
        self.load_ba_table(company.id)
        
        dialog.exec()
        # Refresh main table after closing
        self.load_data()
        
    def load_ba_table(self, company_id):
        session = get_db_session()
        areas = session.query(BusinessArea).filter_by(company_id=company_id).all()
        self.ba_table.setRowCount(0)
        for row, ba in enumerate(areas):
            self.ba_table.insertRow(row)
            self.ba_table.setItem(row, 0, QTableWidgetItem(ba.code))
            self.ba_table.setItem(row, 1, QTableWidgetItem(ba.name))

    def add_business_area(self, dialog, company_id, code, name):
        if len(code) != 2 or not code.isdigit():
             QMessageBox.warning(dialog, "Error", "Code must be 2 digits")
             return
        if not name:
             QMessageBox.warning(dialog, "Error", "Name required")
             return
             
        session = get_db_session()
        
        # Check uniqueness within company? Maybe global uniqueness?
        # User requirement said "2-digit code (e.g. 10) under the Company".
        # So likely unique per company.
        existing = session.query(BusinessArea).filter_by(company_id=company_id, code=code).first()
        if existing:
            QMessageBox.warning(dialog, "Error", "Code already exists in this company")
            return
            
        try:
            ba = BusinessArea(code=code, name=name, company_id=company_id)
            session.add(ba)
            session.commit()
            
            # Refresh list
            self.load_ba_table(company_id)
            # Clear inputs (hacky way since we don't have ref to inputs here easily unless passed)
            # Actually we didn't pass inputs to clear them. 
            # Ideally we'd structure this better, but let's just show success
            # QMessageBox.information(dialog, "Success", "Business Area Added")
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
