from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, 
                             QLineEdit, QTimeEdit, QPushButton, QMessageBox, QGroupBox, 
                             QGridLayout, QLabel, QComboBox, QDateEdit)
from PyQt6.QtCore import QTime, QDate, Qt
from services.leave_service import LeaveService
from services.attendance_service import AttendanceService
from datetime import date
from config import Config

class LeaveRequestDialog(QDialog):
    def __init__(self, parent, session, employee):
        super().__init__(parent)
        self.session = session
        self.employee = employee
        self.setWindowTitle(f"Leave Management - {employee.full_name}")
        self.resize(500, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Balance Section
        balance = LeaveService.get_leave_balance(self.session, self.employee.id, date.today().year)
        
        bal_group = QGroupBox("Leave Balances (Year To Date)")
        bal_layout = QGridLayout()
        row = 0
        for l_type, stats in balance.items():
            bal_layout.addWidget(QLabel(f"<b>{l_type}</b>:"), row, 0)
            bal_layout.addWidget(QLabel(f"Quota: {stats['quota']}"), row, 1)
            bal_layout.addWidget(QLabel(f"Used: {stats['used']}"), row, 2)
            bal_layout.addWidget(QLabel(f"Remaining: {stats['remaining']}"), row, 3)
            row += 1
        bal_group.setLayout(bal_layout)
        layout.addWidget(bal_group)
        
        # 2. Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_short_leave_tab(), "Short Leave")
        tabs.addTab(self.create_full_leave_tab(), "Full Day Leave")
        layout.addWidget(tabs)
        
    def create_short_leave_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        
        self.reason_short = QLineEdit()
        time_fmt = Config.get_qt_time_fmt()

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat(time_fmt)
        self.start_time.setTime(QTime.currentTime())
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat(time_fmt)
        self.end_time.setTime(QTime.currentTime().addSecs(1800)) # 30 mins default
        
        form.addRow("Reason:", self.reason_short)
        form.addRow("Start Time:", self.start_time)
        form.addRow("End Time:", self.end_time)
        
        btn = QPushButton("Request Short Leave")
        btn.clicked.connect(self.submit_short_leave)
        form.addRow(btn)
        
        return widget
        
    def create_full_leave_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        
        self.l_type_combo = QComboBox()
        self.l_type_combo.addItems(["Annual", "Sick", "Casual", "Unpaid"])
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        self.reason_full = QLineEdit()
        
        form.addRow("Type:", self.l_type_combo)
        form.addRow("Start Date:", self.start_date)
        form.addRow("End Date:", self.end_date)
        form.addRow("Reason:", self.reason_full)
        
        btn = QPushButton("Request Full Leave")
        btn.clicked.connect(self.submit_full_leave)
        form.addRow(btn)
        
        return widget
        
    def submit_short_leave(self):
        reason = self.reason_short.text()
        if not reason:
            QMessageBox.warning(self, "Error", "Reason required")
            return
            
        res = AttendanceService.record_short_leave(
            self.session,
            self.employee.attendance_code,
            reason,
            self.start_time.time().toPyTime(),
            self.end_time.time().toPyTime()
        )
        
        self.handle_result(res)
        
    def submit_full_leave(self):
        reason = self.reason_full.text()
        if not reason: # Is reason strict? User wants "user could decide".
            # Usually required for records.
            pass 
            
        res = LeaveService.submit_leave_request(
            self.session,
            self.employee.id,
            self.l_type_combo.currentText(),
            self.start_date.date().toPyDate(),
            self.end_date.date().toPyDate(),
            reason
        )
        
        self.handle_result(res)
        
    def handle_result(self, res):
        if res['success']:
            QMessageBox.information(self, "Success", res['message'])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", res['message'])
