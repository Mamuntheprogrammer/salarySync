from ui.btn_styles import btn_small_delete, btn_primary, btn_small_edit, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QFormLayout, QMessageBox, QHeaderView, QComboBox, 
                             QLineEdit, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import Bonus, Employee

class BonusManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Bonus Manager</h2>"))
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)
        
        btn_add = QPushButton("Add Bonus")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_dialog(None))
        header.addStretch()
        header.addWidget(btn_refresh)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(["Employee", "Period", "Type", "Amount", "Description", "Actions", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 160)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        bonuses = session.query(Bonus).order_by(Bonus.year.desc(), Bonus.month.desc()).all()
        
        self.table.setRowCount(0)
        for row, b in enumerate(bonuses):
            self.table.insertRow(row)
            
            emp_name = f"{b.employee.id} - {b.employee.full_name}" if b.employee else "Unknown"
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            
            period_str = f"{b.year}-{b.month:02d}"
            self.table.setItem(row, 1, QTableWidgetItem(period_str))
            
            type_str = "Percentage" if b.is_percentage else "Fixed Amount"
            self.table.setItem(row, 2, QTableWidgetItem(type_str))
            
            amount_str = f"{b.amount}%" if b.is_percentage else f"{b.amount:.2f}"
            self.table.setItem(row, 3, QTableWidgetItem(amount_str))
            
            self.table.setItem(row, 4, QTableWidgetItem(b.description or ""))
            
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
            btn_delete.clicked.connect(lambda ch, x=b: self.delete_bonus(x))
            action_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 5, action_widget)
            self.table.setItem(row, 6, QTableWidgetItem("")) # Empty spacer
            
    def delete_bonus(self, bonus):
        confirm = QMessageBox.question(self, "Confirm", "Delete this bonus record?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Bonus).filter(Bonus.id == bonus.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self, bonus_obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Bonus" if bonus_obj else "Add Bonus")
        form = QFormLayout(dialog)
        
        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} - {e.full_name}", e.id)
            
        if bonus_obj and bonus_obj.employee_id:
             idx = emp_combo.findData(bonus_obj.employee_id)
             if idx >= 0: emp_combo.setCurrentIndex(idx)
             
        current_date = QDate.currentDate()
            
        month_spin = QSpinBox()
        month_spin.setRange(1, 12)
        if bonus_obj:
            month_spin.setValue(bonus_obj.month)
        else:
            month_spin.setValue(current_date.month())
            
        year_spin = QSpinBox()
        year_spin.setRange(2000, 2100)
        if bonus_obj:
            year_spin.setValue(bonus_obj.year)
        else:
            year_spin.setValue(current_date.year())
            
        type_combo = QComboBox()
        type_combo.addItems(["Fixed Amount", "Percentage"])
        if bonus_obj and bonus_obj.is_percentage:
            type_combo.setCurrentText("Percentage")
            
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.0, 1000000.0)
        amount_spin.setDecimals(2)
        if bonus_obj:
            amount_spin.setValue(bonus_obj.amount)
            
        desc_input = QLineEdit()
        if bonus_obj: desc_input.setText(bonus_obj.description or "")
        
        form.addRow("Employee:", emp_combo)
        form.addRow("Month:", month_spin)
        form.addRow("Year:", year_spin)
        form.addRow("Type:", type_combo)
        form.addRow("Amount:", amount_spin)
        form.addRow("Description:", desc_input)
        
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_bonus(dialog, bonus_obj, {
            "employee_id": emp_combo.currentData(),
            "month": month_spin.value(),
            "year": year_spin.value(),
            "amount": amount_spin.value(),
            "is_percentage": type_combo.currentText() == "Percentage",
            "description": desc_input.text()
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_bonus(self, dialog, bonus_obj, data):
        session = get_db_session()
        try:
            if data['amount'] < 0:
                raise ValueError("Amount cannot be negative.")
                
            if bonus_obj:
                b = session.get(Bonus, bonus_obj.id)
                b.employee_id = data['employee_id']
                b.month = data['month']
                b.year = data['year']
                b.amount = data['amount']
                b.is_percentage = data['is_percentage']
                b.description = data['description']
            else:
                b = Bonus(**data)
                session.add(b)
                
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
