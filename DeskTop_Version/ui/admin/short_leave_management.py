from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QFormLayout, QMessageBox, QHeaderView, QComboBox, 
                             QDateEdit, QTimeEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate, QTime
from database import get_db_session
from models import ShortLeave, Employee
from datetime import datetime

class ShortLeaveManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Short Leave Manager</h2>"))
        
        btn_add = QPushButton("Add Short Leave")
        btn_add.clicked.connect(self.add_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Employee", "Start Time", "End Time", "Reason", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        leaves = session.query(ShortLeave).order_by(ShortLeave.date.desc()).all()
        
        self.table.setRowCount(0)
        for row, l in enumerate(leaves):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(l.date.strftime("%Y-%m-%d")))
            
            emp_name = f"{l.employee.attendance_code} - {l.employee.full_name}" if l.employee else "Unknown"
            self.table.setItem(row, 1, QTableWidgetItem(emp_name))
            
            self.table.setItem(row, 2, QTableWidgetItem(l.start_time.strftime("%H:%M")))
            self.table.setItem(row, 3, QTableWidgetItem(l.end_time.strftime("%H:%M")))
            self.table.setItem(row, 4, QTableWidgetItem(l.reason or ""))
            self.table.setItem(row, 5, QTableWidgetItem(l.status))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_delete = QPushButton("Delete")
            btn_delete.setStyleSheet("background-color: #f44336; color: white;")
            btn_delete.clicked.connect(lambda ch, x=l: self.delete_leave(x))
            action_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 6, action_widget)
            
    def delete_leave(self, leave):
        confirm = QMessageBox.question(self, "Confirm", "Delete this short leave record?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(ShortLeave).filter(ShortLeave.id == leave.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Short Leave")
        form = QFormLayout(dialog)
        
        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.attendance_code} - {e.full_name}", e.id)
            
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        
        start_input = QTimeEdit()
        start_input.setTime(QTime.currentTime())
        
        end_input = QTimeEdit()
        end_input.setTime(QTime.currentTime().addSecs(3600)) # Default 1 hour
        
        reason_input = QLineEdit()
        
        status_combo = QComboBox()
        status_combo.addItems(["Pending", "Approved", "Rejected"])
        
        form.addRow("Employee:", emp_combo)
        form.addRow("Date:", date_input)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Reason:", reason_input)
        form.addRow("Status:", status_combo)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_leave(dialog, {
            "employee_id": emp_combo.currentData(),
            "date": date_input.date().toPyDate(),
            "start_time": start_input.time().toPyTime(),
            "end_time": end_input.time().toPyTime(),
            "reason": reason_input.text(),
            "status": status_combo.currentText()
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_leave(self, dialog, data):
        session = get_db_session()
        try:
            l = ShortLeave(**data)
            session.add(l)
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
