from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox, QDoubleSpinBox, QTimeEdit)
from PyQt6.QtCore import Qt, QTime
from database import get_db_session
from database import get_db_session
from models import Employee, Company, BusinessArea, Shift, Designation, DesignationSubcategory
from services.employee_service import EmployeeService

class EmployeeManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Employee Management</h2>"))
        
        btn_add = QPushButton("Add Employee")
        btn_add.clicked.connect(self.add_employee_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Company", "Area", "Shift", "Designation", "Salary", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Fix underflow
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        employees = session.query(Employee).all()
        
        self.table.setRowCount(0)
        for row, emp in enumerate(employees):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(emp.attendance_code))
            self.table.setItem(row, 1, QTableWidgetItem(emp.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(emp.company.name if emp.company else "-"))
            self.table.setItem(row, 3, QTableWidgetItem(emp.business_area.name if emp.business_area else "-"))
            
            shift_name = emp.shift.name if emp.shift else ("Custom" if emp.custom_shift_start else "None")
            shift_name = emp.shift.name if emp.shift else ("Custom" if emp.custom_shift_start else "None")
            self.table.setItem(row, 4, QTableWidgetItem(shift_name))
            
            designation_str = emp.designation.name if emp.designation else "-"
            if emp.designation_subcategory:
                designation_str += f" - {emp.designation_subcategory.name}"
            self.table.setItem(row, 5, QTableWidgetItem(designation_str))
            
            # Salary
            self.table.setItem(row, 6, QTableWidgetItem(str(emp.salary_base)))
            
            # Status
            status_str = "Active" if emp.is_active else "Inactive"
            status_item = QTableWidgetItem(status_str)
            if emp.is_active:
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                 status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 7, status_item)
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            # Edit
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, e=emp: self.edit_employee_dialog(e))
            action_layout.addWidget(btn_edit)
            
            # Toggle Status
            btn_toggle = QPushButton("Deactivate" if emp.is_active else "Activate")
            if emp.is_active:
                btn_toggle.setStyleSheet("background-color: #f44336; color: white;")
            else:
                btn_toggle.setStyleSheet("background-color: #4CAF50; color: white;")
                
            btn_toggle.clicked.connect(lambda ch, e=emp: self.toggle_status(e))
            action_layout.addWidget(btn_toggle)
            
            self.table.setCellWidget(row, 8, action_widget)

    def toggle_status(self, emp):
        action = "deactivate" if emp.is_active else "activate"
        confirm = QMessageBox.question(self, "Confirm", f"Are you sure you want to {action} {emp.full_name}?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            EmployeeService.update_employee(session, emp.id, {"is_active": not emp.is_active})
            self.load_data()

                    
    def edit_employee_dialog(self, emp):
        session = get_db_session()
        companies = session.query(Company).all()
        shifts = session.query(Shift).all()
        designations = session.query(Designation).all()
        
        # Ensure session is fresh or re-attach objects?
        # Better to query selects fresh.
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {emp.full_name}")
        form = QFormLayout(dialog)
        
        # Style
        combo_style = "QComboBox { padding: 5px; border: 1px solid #ccc; background: white; }"
        
        name_input = QLineEdit(emp.full_name)
        
        # Company
        company_combo = QComboBox()
        company_combo.setStyleSheet(combo_style)
        
        # Business Area
        ba_combo = QComboBox()
        ba_combo.setStyleSheet(combo_style)
        
        selected_co_idx = 0
        for i, c in enumerate(companies):
            company_combo.addItem(f"{c.code} - {c.name}", c.id)
            if c.id == emp.company_id:
                selected_co_idx = i
        company_combo.setCurrentIndex(selected_co_idx)
        
        # Update BA logic
        def update_ba():
            ba_combo.clear()
            cid = company_combo.currentData()
            if cid:
                bas = session.query(BusinessArea).filter_by(company_id=cid).all()
                sel_ba_idx = -1
                for i, ba in enumerate(bas):
                    ba_combo.addItem(f"{ba.code} - {ba.name}", ba.id)
                    if ba.id == emp.business_area_id:
                        sel_ba_idx = i
                if sel_ba_idx >= 0:
                    ba_combo.setCurrentIndex(sel_ba_idx)
                    
        company_combo.currentIndexChanged.connect(update_ba)
        update_ba() # Initialize
        
        salary_input = QDoubleSpinBox()
        salary_input.setRange(0, 1000000)
        salary_input.setValue(emp.salary_base)
        
        # Shift
        shift_combo = QComboBox()
        shift_combo.setStyleSheet(combo_style)
        shift_combo.addItem("None", None)
        sel_shift_idx = 0
        for i, s in enumerate(shifts):
            shift_combo.addItem(f"{s.name} ({s.start_time}-{s.end_time})", s.id)
            if emp.shift_id and s.id == emp.shift_id:
                sel_shift_idx = i + 1
        shift_combo.setCurrentIndex(sel_shift_idx)

        # Custom Shift Times
        custom_start = QTimeEdit()
        custom_start.setDisplayFormat("HH:mm:ss")
        if emp.custom_shift_start:
            custom_start.setTime(QTime(emp.custom_shift_start.hour, emp.custom_shift_start.minute, emp.custom_shift_start.second))
        
        custom_end = QTimeEdit()
        custom_end.setDisplayFormat("HH:mm:ss")
        if emp.custom_shift_end:
             custom_end.setTime(QTime(emp.custom_shift_end.hour, emp.custom_shift_end.minute, emp.custom_shift_end.second))
             
        # Toggle based on shift? Or allow override?
        # If shift is None, we need these.
        def toggle_custom():
             is_custom = shift_combo.currentData() is None
             custom_start.setEnabled(is_custom)
             custom_end.setEnabled(is_custom)
             
        shift_combo.currentIndexChanged.connect(toggle_custom)
        toggle_custom()
        
        # Designation
        deg_combo = QComboBox()
        deg_combo.setStyleSheet(combo_style)
        deg_combo.addItem("None", None)
        sel_deg_idx = 0
        for i, d in enumerate(designations):
            deg_combo.addItem(d.name, d.id)
            if emp.designation_id and d.id == emp.designation_id:
                sel_deg_idx = i + 1
        deg_combo.setCurrentIndex(sel_deg_idx)
        
        # Subcategory
        sub_combo = QComboBox()
        sub_combo.setStyleSheet(combo_style)
        
        def update_subs():
            sub_combo.clear()
            sub_combo.addItem("None", None)
            did = deg_combo.currentData()
            if did:
                subs = session.query(DesignationSubcategory).filter_by(designation_id=did).all()
                sel_sub_idx = 0
                for i, s in enumerate(subs):
                    sub_combo.addItem(s.name, s.id)
                    if emp.designation_subcategory_id and s.id == emp.designation_subcategory_id:
                        sel_sub_idx = i + 1
                sub_combo.setCurrentIndex(sel_sub_idx)
        
        deg_combo.currentIndexChanged.connect(update_subs)
        update_subs()
        
        form.addRow("Name:", name_input)
        form.addRow("Company:", company_combo)
        form.addRow("Business Area:", ba_combo)
        form.addRow("Salary:", salary_input)
        form.addRow("Shift:", shift_combo)
        form.addRow("Custom Start:", custom_start)
        form.addRow("Custom End:", custom_end)

        form.addRow("Designation:", deg_combo)
        form.addRow("Subcategory:", sub_combo)
        
        btn_save = QPushButton("Update")
        btn_save.clicked.connect(lambda: self.save_edit(dialog, emp.id, {
            "full_name": name_input.text(),
            "company_id": company_combo.currentData(),
            "business_area_id": ba_combo.currentData(),
            "salary_base": salary_input.value(),
            "shift_id": shift_combo.currentData(),
            "custom_shift_start": custom_start.time().toPyTime() if shift_combo.currentData() is None else None,
            "custom_shift_end": custom_end.time().toPyTime() if shift_combo.currentData() is None else None,
            "designation_id": deg_combo.currentData(),
            "designation_subcategory_id": sub_combo.currentData()
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_edit(self, dialog, emp_id, data):
        session = get_db_session()
        try:
            # We already have update_employee in service, let's use it
            # But the service expects "data" dict. 
            # Does update_employee handle validation? Yes.
            
            EmployeeService.update_employee(session, emp_id, data)
            QMessageBox.information(dialog, "Success", "Employee Updated")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def add_employee_dialog(self):
        session = get_db_session()
        companies = session.query(Company).all()
        shifts = session.query(Shift).all()
        designations = session.query(Designation).all()
        
        if not companies:
            QMessageBox.warning(self, "Error", "Please create a Company first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Employee")
        form = QFormLayout(dialog)
        
        # Style for dropdowns
        combo_style = """
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
                color: #333;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #2196F3;
                selection-color: white;
            }
        """
        
        name_input = QLineEdit()
        
        # Company Dropdown
        company_combo = QComboBox()
        company_combo.setStyleSheet(combo_style)
        for c in companies:
            company_combo.addItem(f"{c.code} - {c.name}", c.id)
            
        # Business Area Dropdown (Should filter by company, simplified for now to show all or handled by signal)
        # For MVP, let's just show all business areas or just warn if none
        # Better: Logic to populate areas based on company selection
        ba_combo = QComboBox()
        ba_combo.setStyleSheet(combo_style)
        # Initial population
        self.update_ba_combo(session, company_combo.currentData(), ba_combo)
        company_combo.currentIndexChanged.connect(lambda: self.update_ba_combo(session, company_combo.currentData(), ba_combo))
        
        salary_input = QDoubleSpinBox()
        salary_input.setRange(0, 1000000)
        salary_input.setValue(50000)
        
        shift_combo = QComboBox()
        shift_combo.setStyleSheet(combo_style)
        shift_combo.addItem("None", None)
        for s in shifts:
            shift_combo.addItem(f"{s.name} ({s.start_time}-{s.end_time})", s.id)
            
        custom_start = QTimeEdit()
        custom_start.setDisplayFormat("HH:mm:ss")
        custom_end = QTimeEdit()
        custom_end.setDisplayFormat("HH:mm:ss")
        
        def toggle_custom_add():
             is_custom = shift_combo.currentData() is None
             custom_start.setEnabled(is_custom)
             custom_end.setEnabled(is_custom)
             
        shift_combo.currentIndexChanged.connect(toggle_custom_add)
        toggle_custom_add()
            
        # Designation Combo
        deg_combo = QComboBox()
        deg_combo.setStyleSheet(combo_style)
        deg_combo.addItem("None", None)
        for d in designations:
            deg_combo.addItem(d.name, d.id)
            
        # Subcategory Combo
        sub_combo = QComboBox()
        sub_combo.setStyleSheet(combo_style)
        
        # Connect deg change to sub update
        def update_subs():
            sub_combo.clear()
            sub_combo.addItem("None", None)
            deg_id = deg_combo.currentData()
            if deg_id:
                subs = session.query(DesignationSubcategory).filter_by(designation_id=deg_id).all()
                for s in subs:
                    sub_combo.addItem(s.name, s.id)
        
        deg_combo.currentIndexChanged.connect(update_subs)
        update_subs()
            
        form.addRow("Full Name:", name_input)
        form.addRow("Company:", company_combo)
        form.addRow("Business Area:", ba_combo)
        form.addRow("Salary:", salary_input)
        form.addRow("Shift:", shift_combo)
        form.addRow("Custom Start:", custom_start)
        form.addRow("Custom End:", custom_end)

        form.addRow("Designation:", deg_combo)
        form.addRow("Subcategory:", sub_combo)
        
        btn_save = QPushButton("Create Employee")
        btn_save.clicked.connect(lambda: self.save_employee(dialog, {
            "full_name": name_input.text(),
            "company_id": company_combo.currentData(),
            "business_area_id": ba_combo.currentData(),
            "salary_base": salary_input.value(),
            "shift_id": shift_combo.currentData(),
            "custom_shift_start": custom_start.time().toPyTime() if shift_combo.currentData() is None else None,
            "custom_shift_end": custom_end.time().toPyTime() if shift_combo.currentData() is None else None,
            "designation_id": deg_combo.currentData(),
            "designation_subcategory_id": sub_combo.currentData()
            # Simplified mock for business area checks
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def update_ba_combo(self, session, company_id, ba_combo):
        ba_combo.clear()
        if company_id:
            bas = session.query(BusinessArea).filter_by(company_id=company_id).all()
            if not bas:
                # If no BA, create a default one? Or warn?
                # For demo, if no BA exists, we might get stuck.
                # Let's auto-create a default BA for the company if none exists
                if not bas:
                    default_ba = BusinessArea(code="01", name="General", company_id=company_id)
                    session.add(default_ba)
                    session.commit()
                    bas = [default_ba]
            
            for ba in bas:
                ba_combo.addItem(f"{ba.code} - {ba.name}", ba.id)

    def save_employee(self, dialog, data):
        if not data['full_name']:
             QMessageBox.warning(dialog, "Error", "Name required")
             return
             
        session = get_db_session()
        try:
            emp = EmployeeService.create_employee(session, data)
            QMessageBox.information(dialog, "Success", f"Employee Created!\nCode: {emp.attendance_code}")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
