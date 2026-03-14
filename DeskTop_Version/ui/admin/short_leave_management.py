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
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)
        
        btn_add = QPushButton("Add Short Leave")
        btn_add.clicked.connect(lambda: self.add_dialog(None))
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
            
            emp_name = f"{l.employee.id} - {l.employee.full_name}" if l.employee else "Unknown"
            self.table.setItem(row, 1, QTableWidgetItem(emp_name))
            
            self.table.setItem(row, 2, QTableWidgetItem(l.start_time.strftime("%H:%M")))
            self.table.setItem(row, 3, QTableWidgetItem(l.end_time.strftime("%H:%M")))
            self.table.setItem(row, 4, QTableWidgetItem(l.reason or ""))
            self.table.setItem(row, 5, QTableWidgetItem(l.status))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=l: self.add_dialog(x))
            action_layout.addWidget(btn_edit)
            
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

    def add_dialog(self, leave_obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Short Leave" if leave_obj else "Add Short Leave")
        form = QFormLayout(dialog)
        
        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} - {e.full_name}", e.id)
            
        if leave_obj and leave_obj.employee_id:
             idx = emp_combo.findData(leave_obj.employee_id)
             if idx >= 0: emp_combo.setCurrentIndex(idx)
            
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        if leave_obj:
            date_input.setDate(leave_obj.date)
        else:
            date_input.setDate(QDate.currentDate())
        
        start_input = QTimeEdit()
        if leave_obj:
            start_input.setTime(QTime(leave_obj.start_time.hour, leave_obj.start_time.minute))
        else:
            start_input.setTime(QTime.currentTime())
        
        end_input = QTimeEdit()
        if leave_obj:
             end_input.setTime(QTime(leave_obj.end_time.hour, leave_obj.end_time.minute))
        else:
             end_input.setTime(QTime.currentTime().addSecs(3600))
        
        reason_input = QLineEdit()
        if leave_obj: reason_input.setText(leave_obj.reason or "")
        
        status_combo = QComboBox()
        status_combo.addItems(["Pending", "Approved", "Rejected"])
        if leave_obj: status_combo.setCurrentText(leave_obj.status)
        
        form.addRow("Employee:", emp_combo)
        form.addRow("Date:", date_input)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Reason:", reason_input)
        form.addRow("Status:", status_combo)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_leave(dialog, leave_obj, {
            "employee_id": emp_combo.currentData(),
            "date": date_input.date().toPyDate(),
            "start_time": start_input.time().toPyTime(),
            "end_time": end_input.time().toPyTime(),
            "reason": reason_input.text(),
            "status": status_combo.currentText()
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_leave(self, dialog, leave_obj, data):
        session = get_db_session()
        try:
            if leave_obj:
                l = session.get(ShortLeave, leave_obj.id)
                l.employee_id = data['employee_id']
                l.date = data['date']
                l.start_time = data['start_time']
                l.end_time = data['end_time']
                l.reason = data['reason']
                l.status = data['status']
            else:
                l = ShortLeave(**data)
                session.add(l)
                
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
