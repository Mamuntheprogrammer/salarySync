from PyQt6.QtWidgets import (QComboBox, QDateEdit, QDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, 
                             QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QTabWidget, QTimeEdit, 
                             QVBoxLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from models import Employee
from database import get_db_session
from config import Config
from datetime import date

class EmployeeTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Employee Attendance Terminal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Display
        # Input Container
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        # Display
        self.code_display = QLineEdit()
        self.code_display.setPlaceholderText("Enter Attendance Code or Employee ID")
        self.code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_display.setFont(QFont("Arial", 24))
        self.code_display.setEchoMode(QLineEdit.EchoMode.Password)
        self.code_display.setReadOnly(False) # Allow keyboard input
        self.code_display.setStyleSheet("border: none; padding: 10px; background: transparent;")
        
        input_layout.addWidget(self.code_display)
        
        # Toggle Button
        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedWidth(60) 
        self.toggle_btn.setFont(QFont("Arial", 20))
        self.toggle_btn.setToolTip("Show/Hide Password")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #777777;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                padding-right: 10px;
            }
            QPushButton:hover {
                color: #333333;
                background-color: #f0f0f0;
            }
        """)
        
        def toggle_password():
            if self.code_display.echoMode() == QLineEdit.EchoMode.Password:
                self.code_display.setEchoMode(QLineEdit.EchoMode.Normal)
                self.toggle_btn.setText("🔒")
            else:
                self.code_display.setEchoMode(QLineEdit.EchoMode.Password)
                self.toggle_btn.setText("👁")
                
        self.toggle_btn.clicked.connect(toggle_password)
        input_layout.addWidget(self.toggle_btn)
        
        layout.addWidget(input_container)
        
        # Keypad
        grid_layout = QGridLayout()
        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2),
            ('Clear', 3, 0), ('0', 3, 1), ('X', 3, 2)
        ]
        
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedSize(80, 60)
            btn.clicked.connect(lambda checked, t=text: self.on_keypad_click(t))
            grid_layout.addWidget(btn, row, col)
            
        layout.addLayout(grid_layout)
        
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
        self.btn_leave = QPushButton("Manage Leave")
        self.btn_leave.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 12px;")
        self.btn_leave.clicked.connect(self.open_leave_management)
        layout.addWidget(self.btn_leave)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.status_label)
        
    def on_keypad_click(self, text):
        current = self.code_display.text()
        if text == 'Clear':
            self.code_display.clear()
        elif text == 'X':
            self.code_display.setText(current[:-1])
        else:
            self.code_display.setText(current + text)
                
    def get_code(self):
        code = self.code_display.text().strip()
        if not code:
            self.status_label.setText("Please enter an Attendance Code or Employee ID")
            return None
        return code
        
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
        
    def open_leave_management(self):
        # Authenticate first using the keypad display
        code = self.get_code()
        if not code: return
        
        session = get_db_session()
        employee = session.query(Employee).filter_by(attendance_code=code).first()
        if not employee and code.isdigit():
            employee = session.query(Employee).filter_by(id=int(code)).first()
        if not employee:
            self.status_label.setText("Invalid Code / Employee ID")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            return
            
        from ui.dialogs.leave_request_dialog import LeaveRequestDialog
        dialog = LeaveRequestDialog(self, session, employee)
        if dialog.exec():
            # If dialog accepted (success), define post-action
            self.status_label.setText("Leave request action completed.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.code_display.clear()
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def handle_result(self, result):
        if result['success']:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            self.code_display.clear()
            # Clear status after 3 seconds
            QTimer.singleShot(5000, lambda: self.status_label.setText(""))
        else:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
