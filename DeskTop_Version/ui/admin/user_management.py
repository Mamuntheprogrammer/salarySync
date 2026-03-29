from ui.btn_styles import btn_small_edit, btn_small_delete, btn_small_neutral, btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog,
                             QLineEdit, QFormLayout, QMessageBox, QComboBox)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)

        btn_add = QPushButton("＋  Create User")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_user_dialog(None))

        layout.addWidget(make_page_header("User Manager",
                                          "Manage admin panel user accounts and roles",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Employee", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[1, 2, 3],
                             fixed_cols={0: 50, 4: 220})
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

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

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=user: self.add_user_dialog(x))
            al.addWidget(b1)

            b2 = QPushButton("Pwd")
            b2.setStyleSheet(btn_small_neutral())
            b2.clicked.connect(lambda _, u=user: self.reset_password_dialog(u))
            al.addWidget(b2)

            b3 = QPushButton("Delete")
            b3.setStyleSheet(btn_small_delete())
            b3.clicked.connect(lambda _, x=user: self.delete_user(x))
            al.addWidget(b3)

            self.table.setCellWidget(row, 4, aw)

    def delete_user(self, user):
        if QMessageBox.question(self, "Confirm", f"Delete user '{user.username}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(AdminUser).filter(AdminUser.id == user.id).delete()
            session.commit()
            self.load_data()

    def add_user_dialog(self, user_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit User" if user_obj else "Create User")
        style_dialog(dialog, min_width=400)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        username_input = QLineEdit()
        if user_obj:
            username_input.setText(user_obj.username)
            username_input.setEnabled(False)
        else:
            username_input.setPlaceholderText("Enter username")

        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setPlaceholderText("Leave blank to keep existing" if user_obj else "Enter password")

        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        if user_obj:
            role_combo.setCurrentText(user_obj.role)

        session = get_db_session()
        emp_combo = QComboBox()
        emp_combo.addItem("None (System Admin)", None)
        for emp in session.query(Employee).all():
            emp_combo.addItem(f"{emp.id} — {emp.full_name}", emp.id)
        if user_obj and user_obj.employee_id:
            idx = emp_combo.findData(user_obj.employee_id)
            if idx >= 0:
                emp_combo.setCurrentIndex(idx)

        form.addRow("Username:", username_input)
        form.addRow("Password:", password_input)
        form.addRow("Role:", role_combo)
        form.addRow("Employee Link:", emp_combo)

        btn_save = QPushButton("Save User")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_user(dialog, user_obj,
                                                         username_input.text(),
                                                         password_input.text(),
                                                         role_combo.currentText(),
                                                         emp_combo.currentData()))
        form.addRow("", btn_save)
        dialog.exec()

    def save_user(self, dialog, user_obj, username, password, role, employee_id):
        if not username:
            QMessageBox.warning(dialog, "Validation", "Username is required")
            return
        if not user_obj and not password:
            QMessageBox.warning(dialog, "Validation", "Password is required for new user")
            return
        session = get_db_session()
        try:
            if user_obj:
                u = session.get(AdminUser, user_obj.id)
                u.role = role
                u.employee_id = employee_id
                if password:
                    UserService.reset_password(session, u.id, password)
                session.commit()
            else:
                UserService.create_user(session, username, password, role, employee_id)
            QMessageBox.information(dialog, "Success", "User saved successfully.")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def reset_password_dialog(self, user):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reset Password — {user.username}")
        style_dialog(dialog, min_width=380)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setPlaceholderText("New password")
        form.addRow("New Password:", password_input)

        btn_reset = QPushButton("Reset Password")
        btn_reset.setStyleSheet(btn_primary())
        btn_reset.clicked.connect(lambda: self._do_reset(dialog, user.id, password_input.text()))
        form.addRow("", btn_reset)
        dialog.exec()

    def _do_reset(self, dialog, user_id, new_password):
        if not new_password:
            QMessageBox.warning(dialog, "Validation", "New password cannot be empty")
            return
        session = get_db_session()
        try:
            UserService.reset_password(session, user_id, new_password)
            QMessageBox.information(dialog, "Success", "Password reset successfully.")
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
