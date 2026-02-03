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
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)
        
        btn_add = QPushButton("Add Company")
        btn_add.clicked.connect(lambda: self.add_company_dialog(None))
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
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_manage = QPushButton("Areas")
            btn_manage.clicked.connect(lambda checked, c=comp: self.manage_areas_dialog(c))
            action_layout.addWidget(btn_manage)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=comp: self.add_company_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("color: red")
            btn_del.clicked.connect(lambda ch, x=comp: self.delete_company(x))
            action_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row, 4, action_widget)

    def delete_company(self, company):
        confirm = QMessageBox.question(self, "Confirm", f"Delete company '{company.name}'? This will delete all associated business areas and data.", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Company).filter_by(id=company.id).delete()
            session.commit()
            self.load_data()
            
    def add_company_dialog(self, company_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Company" if company_obj else "Add Company")
        form = QFormLayout(dialog)
        
        code_input = QLineEdit()
        code_input.setMaxLength(4)
        code_input.setPlaceholderText("3 or 4 digit code")
        if company_obj:
            code_input.setText(company_obj.code)
            # Code usually shouldn't change as it links things, but allowing for now or could disable
        
        name_input = QLineEdit()
        if company_obj: name_input.setText(company_obj.name)
        
        form.addRow("Company Code:", code_input)
        form.addRow("Company Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_company(dialog, company_obj, code_input.text(), name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_company(self, dialog, company_obj, code, name):
        if len(code) < 3 or len(code) > 4:
            QMessageBox.warning(dialog, "Error", "Code must be 3 or 4 characters")
            return
            
        if not name:
            QMessageBox.warning(dialog, "Error", "Name is required")
            return
            
        session = get_db_session()
        try:
            exists_q = session.query(Company).filter_by(code=code)
            if company_obj:
                exists_q = exists_q.filter(Company.id != company_obj.id)
                
            if exists_q.first():
                QMessageBox.warning(dialog, "Error", "Company Code already exists")
                return
            
            if company_obj:
                c = session.get(Company, company_obj.id)
                c.code = code
                c.name = name
            else:
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
        dialog.resize(600, 450)
        layout = QVBoxLayout(dialog)
        
        # Add Area Form
        form_layout = QHBoxLayout()
        
        code_input = QLineEdit()
        code_input.setMaxLength(2)
        code_input.setPlaceholderText("Code (2 digits)")
        code_input.setFixedWidth(100)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Area Name")
        
        # We need a way to know if we are editing an existing item from the form
        # Instead of complex state, let's keep the form for ADD ONLY and use Dialog for Edit.
        # So this form stays as "Add New".
        
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(lambda: self.save_business_area(dialog, None, company.id, code_input.text(), name_input.text()))
        
        form_layout.addWidget(code_input)
        form_layout.addWidget(name_input)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)
        
        # List Existing Areas
        self.ba_table = QTableWidget()
        self.ba_table.setColumnCount(3) # Added Action
        self.ba_table.setHorizontalHeaderLabels(["Code", "Name", "Action"])
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
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=ba: self.edit_ba_dialog(x, company_id))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("color: red")
            btn_del.clicked.connect(lambda ch, x=ba: self.delete_business_area(x, company_id))
            action_layout.addWidget(btn_del)
            
            self.ba_table.setCellWidget(row, 2, action_widget)

    def delete_business_area(self, ba, company_id):
        confirm = QMessageBox.question(None, "Confirm", f"Delete business area '{ba.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(BusinessArea).filter_by(id=ba.id).delete()
            session.commit()
            self.load_ba_table(company_id)

    def edit_ba_dialog(self, ba, company_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Business Area")
        form = QFormLayout(dialog)
        
        code_input = QLineEdit()
        code_input.setMaxLength(2)
        code_input.setText(ba.code)
        
        name_input = QLineEdit()
        name_input.setText(ba.name)
        
        form.addRow("Code:", code_input)
        form.addRow("Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_business_area(dialog, ba, company_id, code_input.text(), name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        self.load_ba_table(company_id)

    def save_business_area(self, dialog, ba_obj, company_id, code, name):
        if len(code) != 2 or not code.isdigit():
             QMessageBox.warning(dialog, "Error", "Code must be 2 digits")
             return
        if not name:
             QMessageBox.warning(dialog, "Error", "Name required")
             return
             
        session = get_db_session()
        
        existing = session.query(BusinessArea).filter_by(company_id=company_id, code=code)
        if ba_obj:
            existing = existing.filter(BusinessArea.id != ba_obj.id)
        
        if existing.first():
            QMessageBox.warning(dialog, "Error", "Code already exists in this company")
            return
            
        try:
            if ba_obj:
                ba = session.get(BusinessArea, ba_obj.id)
                ba.code = code
                ba.name = name
                # Close dialog only if it's the edit dialog (which has a parent)
                # If it's the 'Add' button from main dialog, 'dialog' is main dialog which we shouldn't close.
                # Actually, in add case, 'dialog' is passed as the main dialog. We shouldn't close it.
                # In edit case, 'dialog' is the small popup. We should close it.
                if dialog.windowTitle() == "Edit Business Area":
                    dialog.accept()
                else:
                    # Clear inputs? Would need ref. 
                    pass
            else:
                ba = BusinessArea(code=code, name=name, company_id=company_id)
                session.add(ba)
                # Keep main dialog open
            
            session.commit()
            
            if ba_obj is None:
               # Refresh table
               self.load_ba_table(company_id)

        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
