from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import AdminUser, Employee
from services.user_service import UserService

class UserManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>User Management</h2>"))
        
        btn_add = QPushButton("Create User")
        btn_add.clicked.connect(self.add_user_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Employee", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        users = UserService.get_all_users(session)
        
        self.table.setRowCount(0)
        for row, user in enumerate(users):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.table.setItem(row, 1, QTableWidgetItem(user.username))
            self.table.setItem(row, 2, QTableWidgetItem(user.role))
            
            emp_name = user.employee.full_name if user.employee else "System Admin"
            self.table.setItem(row, 3, QTableWidgetItem(emp_name))
            
            # Action (Reset Password)
            btn_reset = QPushButton("Reset Pwd")
            btn_reset.clicked.connect(lambda checked, u=user: self.reset_password_dialog(u))
            self.table.setCellWidget(row, 4, btn_reset)

    def add_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create User")
        form = QFormLayout(dialog)
        
        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        
        # Employee Selection
        session = get_db_session()
        employees = session.query(Employee).all()
        
        emp_combo = QComboBox()
        emp_combo.addItem("None (System Admin)", None)
        for emp in employees:
            emp_combo.addItem(f"{emp.attendance_code} - {emp.full_name}", emp.id)
            
        form.addRow("Username:", username_input)
        form.addRow("Password:", password_input)
        form.addRow("Role:", role_combo)
        form.addRow("Employee Link:", emp_combo)
        
        btn_save = QPushButton("Create")
        btn_save.clicked.connect(lambda: self.save_user(dialog, 
            username_input.text(), 
            password_input.text(),
            role_combo.currentText(),
            emp_combo.currentData()
        ))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_user(self, dialog, username, password, role, employee_id):
        if not username or not password:
            QMessageBox.warning(dialog, "Error", "Username and Password required")
            return
            
        session = get_db_session()
        try:
            UserService.create_user(session, username, password, role, employee_id)
            QMessageBox.information(dialog, "Success", "User Created")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
            
    def reset_password_dialog(self, user):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reset Password - {user.username}")
        form = QFormLayout(dialog)
        
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("New Password:", password_input)
        
        btn_save = QPushButton("Reset")
        btn_save.clicked.connect(lambda: self.do_reset_password(dialog, user.id, password_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def do_reset_password(self, dialog, user_id, new_password):
        if not new_password: return
        
        session = get_db_session()
        try:
            UserService.reset_password(session, user_id, new_password)
            QMessageBox.information(dialog, "Success", "Password Reset Successfully")
            dialog.accept()
        except Exception as e:
             QMessageBox.critical(dialog, "Error", str(e))
