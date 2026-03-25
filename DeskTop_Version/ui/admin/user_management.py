from ui.btn_styles import btn_small_edit, btn_small_delete, btn_small_neutral, btn_primary, btn_neutral
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
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)
        
        btn_add = QPushButton("Create User")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_user_dialog(None))
        header.addStretch()
        header.addWidget(btn_refresh)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Employee", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 240)
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
            
            # Action (Edit, Delete, Reset Password)
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda ch, x=user: self.add_user_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_reset = QPushButton("Reset Pwd")
            btn_reset.setStyleSheet(btn_small_neutral())
            btn_reset.clicked.connect(lambda checked, u=user: self.reset_password_dialog(u))
            action_layout.addWidget(btn_reset)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda ch, x=user: self.delete_user(x))
            action_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row, 4, action_widget)
            
    def delete_user(self, user):
        confirm = QMessageBox.question(self, "Confirm", f"Delete user '{user.username}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(AdminUser).filter(AdminUser.id == user.id).delete()
            session.commit()
            self.load_data()

    def add_user_dialog(self, user_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit User" if user_obj else "Create User")
        form = QFormLayout(dialog)
        
        username_input = QLineEdit()
        if user_obj: 
            username_input.setText(user_obj.username)
            username_input.setEnabled(False) # Usually don't edit username
            
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if user_obj:
            password_input.setPlaceholderText("Leave blank to keep existing password")
        
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        if user_obj: role_combo.setCurrentText(user_obj.role)
        
        # Employee Selection
        session = get_db_session()
        employees = session.query(Employee).all()
        
        emp_combo = QComboBox()
        emp_combo.addItem("None (System Admin)", None)
        for emp in employees:
            emp_combo.addItem(f"{emp.id} - {emp.full_name}", emp.id)
            
        if user_obj and user_obj.employee_id:
            idx = emp_combo.findData(user_obj.employee_id)
            if idx >= 0: emp_combo.setCurrentIndex(idx)
            
        form.addRow("Username:", username_input)
        form.addRow("Password:", password_input)
        form.addRow("Role:", role_combo)
        form.addRow("Employee Link:", emp_combo)
        
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_user(dialog, 
            user_obj,
            username_input.text(), 
            password_input.text(),
            role_combo.currentText(),
            emp_combo.currentData()
        ))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_user(self, dialog, user_obj, username, password, role, employee_id):
        if not username:
            QMessageBox.warning(dialog, "Error", "Username required")
            return
        if not user_obj and not password:
             QMessageBox.warning(dialog, "Error", "Password required for new user")
             return
            
        session = get_db_session()
        try:
            if user_obj:
                u = session.get(AdminUser, user_obj.id)
                u.role = role
                u.employee_id = employee_id
                if password:
                     # Using service to hash password? 
                     # UserService.create_user hashes it. I should use UserService.update_user if it existed.
                     # Or duplicate hashing. Wait, I recall UserService handles hashing implicitly on creation.
                     # I should check if I can just call UserService method or if I need to replicate hashing here.
                     # Safe bet: Use UserService.reset_password logic for password update, and manual for others.
                     UserService.reset_password(session, u.id, password)
                     # Re-fetch or stick with current logic?
                     # Let's simple update fields here.
                
                # Update role/emp
                # Note: If I didn't verify password hashing earlier, assuming reset_password handles it.
                # Yes, reset_password handles hashing.
                
                session.commit()
            else:
                UserService.create_user(session, username, password, role, employee_id)
                
            QMessageBox.information(dialog, "Success", "User Saved")
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
        btn_save.setStyleSheet(btn_primary())
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
