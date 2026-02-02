from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import get_db_session
from services.user_service import UserService
from config import Config
from services.sync_service import SyncService

class AdminLoginWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container for login form
        container = QFrame()
        container.setStyleSheet("background-color: #f0f0f0; border-radius: 10px; padding: 20px;")
        container.setFixedSize(400, 350)
        container_layout = QVBoxLayout(container)
        
        # Title
        title = QLabel("Admin Portal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        container_layout.addWidget(title)
        
        # Username
        container_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        self.username_input.setStyleSheet("padding: 8px;")
        container_layout.addWidget(self.username_input)
        
        # Password
        container_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 8px;")
        self.password_input.returnPressed.connect(self.handle_login)
        container_layout.addWidget(self.password_input)
        
        # Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.login_btn.clicked.connect(self.handle_login)
        container_layout.addWidget(self.login_btn)
        
        layout.addWidget(container)
        
        # Create default admin if none exists (Development only)
        self.ensure_default_admin()
        
        # Remote DB Status
        self.check_remote_status(layout)

    def check_remote_status(self, layout):
        config = Config.load_config()
        remote_cfg = config.get("remote_db", {})
        
        if remote_cfg.get("enabled") and remote_cfg.get("connection_string"):
            status_label = QLabel("Checking Remote DB...")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status_label)
            
            # Simple sync check (blocking for now, ideal would be async)
            service = SyncService()
            success, _ = service.test_remote_connection(remote_cfg["connection_string"])
            
            if success:
                status_label.setText("🟢 Remote DB Connected")
                status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                status_label.setText("🔴 Remote DB Disconnected")
                status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
             lbl = QLabel("⚪ Remote DB Not Configured")
             lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
             lbl.setStyleSheet("color: gray;")
             layout.addWidget(lbl)
        
    def ensure_default_admin(self):
        session = get_db_session()
        # Check if any user exists
        if not UserService.get_all_users(session):
            # Create default admin
            UserService.create_user(session, "admin", "admin123", "admin")
            print("Default admin created: admin / admin123")
            
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter username and password")
            return
            
        session = get_db_session()
        user = UserService.authenticate(session, username, password)
        
        if user:
            self.open_dashboard(user)
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
            
    def open_dashboard(self, user):
        from .dashboard import AdminDashboard
        dashboard = AdminDashboard(self.main_window, user)
        self.main_window.switch_to_dashboard(dashboard)
