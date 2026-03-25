from ui.btn_styles import btn_small_edit, btn_small_delete, btn_small_neutral, btn_primary, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QFormLayout, QMessageBox, QHeaderView, QComboBox, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import SalaryBreakdown, Employee

class SalaryBreakdownManager(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Salary Breakdown Manager</h2>"))
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)
        
        btn_add = QPushButton("Add Breakdown")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_dialog(None))
        header.addStretch()
        header.addWidget(btn_refresh)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11) # Employee, Year, ValidTo, Basic, HRA, Conveyance, Med, Mobile, Trans, Other, Actions
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().hide()

        self.table.setHorizontalHeaderLabels([
            "Employee", "Year", "Valid To", "Basic", "HRA", 
            "Conveyance", "Medical", "Mobile", "Transportation", 
            "Other", "Actions"
        ])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        breakdowns = session.query(SalaryBreakdown).order_by(SalaryBreakdown.year.desc()).all()
        
        self.table.setRowCount(0)
        for row, b in enumerate(breakdowns):
            self.table.insertRow(row)
            
            emp_name = f"{b.employee.id} - {b.employee.full_name}" if b.employee else "Unknown"
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            
            self.table.setItem(row, 1, QTableWidgetItem(str(b.year)))
            
            valid_to_str = b.valid_to.strftime("%Y-%m-%d") if b.valid_to else ""
            self.table.setItem(row, 2, QTableWidgetItem(valid_to_str))
            self.table.setItem(row, 3, QTableWidgetItem(f"{b.basic:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{b.house_rent_allowance:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{b.conveyance:,.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{b.medical:,.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{b.mobile_bill:,.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"{b.transportation_allowance:,.2f}"))
            self.table.setItem(row, 9, QTableWidgetItem(f"{b.other_allowance:,.2f}"))
            
            # Actions
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda ch, x=b: self.add_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_delete = QPushButton("Delete")
            btn_delete.setStyleSheet(btn_small_delete())
            btn_delete.clicked.connect(lambda ch, x=b: self.delete_breakdown(x))
            action_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 10, action_widget)
            
    def delete_breakdown(self, breakdown):
        confirm = QMessageBox.question(self, "Confirm", "Delete this Salary Breakdown record?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(SalaryBreakdown).filter(SalaryBreakdown.id == breakdown.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self, obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Salary Breakdown" if obj else "Add Salary Breakdown")
        form = QFormLayout(dialog)
        
        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} - {e.full_name}", e.id)
            
        if obj and obj.employee_id:
             idx = emp_combo.findData(obj.employee_id)
             if idx >= 0: emp_combo.setCurrentIndex(idx)
             
        current_date = QDate.currentDate()
            
        year_spin = QSpinBox()
        year_spin.setRange(2000, 2100)
        year_spin.setValue(obj.year if obj else current_date.year())
            
        valid_to_date = QDateEdit()
        valid_to_date.setCalendarPopup(True)
        if obj and obj.valid_to:
            valid_to_date.setDate(QDate(obj.valid_to.year, obj.valid_to.month, obj.valid_to.day))
        else:
            valid_to_date.setDate(QDate(current_date.year(), 12, 31)) # Default to end of year
            
        # Float fields
        def create_money_spin(val=0.0):
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 9999999.99)
            spin.setDecimals(2)
            spin.setValue(val)
            return spin

        basic_spin = create_money_spin(obj.basic if obj else 0.0)
        hra_spin = create_money_spin(obj.house_rent_allowance if obj else 0.0)
        conv_spin = create_money_spin(obj.conveyance if obj else 0.0)
        med_spin = create_money_spin(obj.medical if obj else 0.0)
        mob_spin = create_money_spin(obj.mobile_bill if obj else 0.0)
        trans_spin = create_money_spin(obj.transportation_allowance if obj else 0.0)
        other_spin = create_money_spin(obj.other_allowance if obj else 0.0)
        
        total_lbl = QLabel("0.00")
        total_lbl.setStyleSheet("font-weight: bold;")

        def update_total():
            total = (basic_spin.value() + hra_spin.value() + conv_spin.value() + 
                     med_spin.value() + mob_spin.value() + trans_spin.value() + 
                     other_spin.value())
            total_lbl.setText(f"{total:,.2f}")

        basic_spin.valueChanged.connect(update_total)
        hra_spin.valueChanged.connect(update_total)
        conv_spin.valueChanged.connect(update_total)
        med_spin.valueChanged.connect(update_total)
        mob_spin.valueChanged.connect(update_total)
        trans_spin.valueChanged.connect(update_total)
        other_spin.valueChanged.connect(update_total)
        update_total() # initial

        form.addRow("Employee:", emp_combo)
        form.addRow("Year:", year_spin)
        form.addRow("Valid To:", valid_to_date)
        form.addRow("Basic:", basic_spin)
        form.addRow("House Rent Allowance:", hra_spin)
        form.addRow("Conveyance:", conv_spin)
        form.addRow("Medical:", med_spin)
        form.addRow("Mobile Bill:", mob_spin)
        form.addRow("Transportation:", trans_spin)
        form.addRow("Other Allowance:", other_spin)
        form.addRow("Total Summary:", total_lbl)
        
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_breakdown(dialog, obj, {
            "employee_id": emp_combo.currentData(),
            "year": year_spin.value(),
            "valid_to": valid_to_date.date().toPyDate(),
            "basic": basic_spin.value(),
            "house_rent_allowance": hra_spin.value(),
            "conveyance": conv_spin.value(),
            "medical": med_spin.value(),
            "mobile_bill": mob_spin.value(),
            "transportation_allowance": trans_spin.value(),
            "other_allowance": other_spin.value(),
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_breakdown(self, dialog, obj, data):
        session = get_db_session()
        try:
            # Check if one already exists for this employee and year
            existing = session.query(SalaryBreakdown).filter_by(employee_id=data['employee_id'], year=data['year']).first()
            if existing and (not obj or existing.id != obj.id):
                raise ValueError(f"A Salary Breakdown already exists for this employee in {data['year']}.")

            if obj:
                b = session.get(SalaryBreakdown, obj.id)
                b.employee_id = data['employee_id']
                b.year = data['year']
                b.valid_to = data['valid_to']
                b.basic = data['basic']
                b.house_rent_allowance = data['house_rent_allowance']
                b.conveyance = data['conveyance']
                b.medical = data['medical']
                b.mobile_bill = data['mobile_bill']
                b.transportation_allowance = data['transportation_allowance']
                b.other_allowance = data['other_allowance']
            else:
                b = SalaryBreakdown(**data)
                session.add(b)
                
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
