from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QComboBox, QMessageBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.attendance_service import AttendanceService
from database import get_db_session
from models import Company, BusinessArea, Employee
from services.attendance_service import AttendanceService # Re-import if needed or use from above
from config import Config

class AdminTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_companies()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Admin Attendance Terminal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Container for Selection
        selection_frame = QFrame()
        selection_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9; 
                border-radius: 10px; 
                border: 1px solid #ddd;
            }
            QLabel {
                font-weight: bold;
                color: #333;
                font-size: 14px;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                color: #333;
                min-width: 200px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #2196F3;
                selection-color: white;
                border: 1px solid #ccc;
            }
        """)
        
        # Use Grid Layout for better alignment
        sel_layout = QGridLayout(selection_frame)
        sel_layout.setContentsMargins(20, 20, 20, 20)
        sel_layout.setSpacing(15)
        
        # Company Dropdown
        sel_layout.addWidget(QLabel("Select Company:"), 0, 0)
        self.company_combo = QComboBox()
        self.company_combo.currentIndexChanged.connect(self.on_company_change)
        sel_layout.addWidget(self.company_combo, 0, 1)
        
        # Business Area Dropdown
        sel_layout.addWidget(QLabel("Select Business Area:"), 1, 0)
        self.ba_combo = QComboBox()
        self.ba_combo.currentIndexChanged.connect(self.on_ba_change)
        sel_layout.addWidget(self.ba_combo, 1, 1)
        
        # Employee Dropdown
        sel_layout.addWidget(QLabel("Select Employee:"), 2, 0)
        self.emp_combo = QComboBox()
        self.emp_combo.currentIndexChanged.connect(self.on_emp_change)
        sel_layout.addWidget(self.emp_combo, 2, 1)
        
        layout.addWidget(selection_frame)
        
        # Code Entry (Manual or Auto-populated)
        layout.addWidget(QLabel("ID or Attendance Code:"))
        self.code_display = QLineEdit()
        self.code_display.setPlaceholderText("Enter ID or Attendance Code")
        self.code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_display.setFont(QFont("Arial", 20))
        # No Password Echo Mode (Visible)
        self.code_display.setStyleSheet("padding: 10px; border: 2px solid #2196F3; border-radius: 5px;")
        layout.addWidget(self.code_display)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.btn_in = QPushButton("Clock IN")
        self.btn_in.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; font-size: 14px;")
        self.btn_in.clicked.connect(self.action_clock_in)
        
        self.btn_out = QPushButton("Clock OUT")
        self.btn_out.setStyleSheet("background-color: #f44336; color: white; padding: 15px; font-size: 14px;")
        self.btn_out.clicked.connect(self.action_clock_out)
        
        action_layout.addWidget(self.btn_in)
        action_layout.addWidget(self.btn_out)
        layout.addLayout(action_layout)
        
        # Short Leave Button
        self.btn_leave = QPushButton("Leave Request")
        self.btn_leave.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 12px;")
        self.btn_leave.clicked.connect(self.action_leave_request)
        layout.addWidget(self.btn_leave)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()

    def load_companies(self):
        self.company_combo.blockSignals(True)
        self.company_combo.clear()
        session = get_db_session()
        companies = session.query(Company).all()
        self.company_combo.addItem("- Select Company -", None)
        for c in companies:
            self.company_combo.addItem(f"{c.code} - {c.name}", c.id)
        self.company_combo.blockSignals(False)

    def on_company_change(self):
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("- Select Business Area -", None)
        
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("- Select Employee -", None)
        self.emp_combo.blockSignals(False)
        
        self.code_display.clear()
        
        company_id = self.company_combo.currentData()
        if company_id:
            session = get_db_session()
            bas = session.query(BusinessArea).filter_by(company_id=company_id).all()
            for ba in bas:
                self.ba_combo.addItem(f"{ba.code} - {ba.name}", ba.id)
        
        self.ba_combo.blockSignals(False)
            
    def on_ba_change(self):
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("- Select Employee -", None)
        
        self.code_display.clear()
        
        ba_id = self.ba_combo.currentData()
        if ba_id:
            session = get_db_session()
            emps = session.query(Employee).filter_by(business_area_id=ba_id).all()
            for emp in emps:
                # Store attendance_code as data so it also works for clock-in/out
                self.emp_combo.addItem(f"{emp.id} - {emp.attendance_code} - {emp.full_name}", emp.attendance_code)
        
        self.emp_combo.blockSignals(False)

    def on_emp_change(self):
        code = self.emp_combo.currentData()
        if code:
            self.code_display.setText(code)
        else:
            self.code_display.clear()

    def get_code(self):
        code = self.code_display.text().strip()
        if not code:
            self.status_label.setText("Please enter or select an ID or Attendance Code")
            return None
        return code
        
    # Re-use logic from EmployeeTerminal or Service
    def action_clock_in(self):
        code = self.get_code()
        if not code: return
        session = get_db_session()
        result = AttendanceService.clock_in(session, code)
        self.handle_result(result)
        
    def action_clock_out(self):
        code = self.get_code()
        if not code: return
        session = get_db_session()
        result = AttendanceService.clock_out(session, code)
        self.handle_result(result)
        
    def action_leave_request(self):
        code = self.get_code()
        if not code: return
        
        session = get_db_session()
        employee = session.query(Employee).filter_by(attendance_code=code).first()
        if not employee and code.isdigit():
            employee = session.query(Employee).filter_by(id=int(code)).first()
        if not employee:
             self.status_label.setText("Employee not found")
             return
        
        from ui.dialogs.leave_request_dialog import LeaveRequestDialog
        dialog = LeaveRequestDialog(self, session, employee)
        dialog.exec()
            
    def handle_result(self, result):
        if result['success']:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            # Don't clear code if manual selection, or maybe verify behavior?
            # User might want to clock multiple people.
            # But let's clear for safety/reset.
            self.status_label.setText(f"{result['message']}")
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
        else:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
