from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame, QFormLayout, QApplication, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
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
        # Container for login form
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #ffffff; 
                border-radius: 2px; 
                border: 1px solid #d0d0d0;
            }
        """)
        container.setFixedSize(450, 380)
        
        # Add Shadow Effect using QGraphicsDropShadowEffect instead of CSS
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 30))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(25)
        
        # Title
        title = QLabel("Admin Portal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-family: 'Segoe UI', sans-serif;
                font-size: 26px;
                font-weight: bold;
                margin-bottom: 25px;
            }
        """)
        container_layout.addWidget(title)
        
        # Form Layout replacement with Custom Input Groups
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20) 
        
        def create_input_group(label_text, placeholder, is_password=False):
            group = QFrame()
            group.setStyleSheet("""
                QFrame {
                    background-color: #f9f9f9;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                }
                QFrame:focus-within {
                    border: 1px solid #4CAF50;
                    background-color: #ffffff;
                }
            """)
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(0)
            
            lbl = QLabel(label_text)
            lbl.setFixedWidth(100)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #eeeeee;
                    border: none;
                    border-right: 1px solid #cccccc;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    padding-right: 15px;
                    color: #555555;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'Segoe UI', sans-serif;
                }
            """)
            
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet("""
                QLineEdit {
                    border: none;
                    background-color: transparent;
                    padding: 12px;
                    font-size: 14px;
                }
            """)
            
            group_layout.addWidget(lbl)
            group_layout.addWidget(inp)
            
            if is_password:
                inp.setEchoMode(QLineEdit.EchoMode.Password)
                # Toggle Button
                toggle_btn = QPushButton("👁")
                toggle_btn.setFixedWidth(40)
                toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                toggle_btn.setToolTip("Show/Hide Password")
                toggle_btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background-color: transparent;
                        color: #777777;
                        font-size: 16px;
                        border-top-right-radius: 4px;
                        border-bottom-right-radius: 4px;
                    }
                    QPushButton:hover {
                        color: #333333;
                        background-color: #f0f0f0;
                    }
                """)
                
                def toggle_password():
                    if inp.echoMode() == QLineEdit.EchoMode.Password:
                        inp.setEchoMode(QLineEdit.EchoMode.Normal)
                        toggle_btn.setText("🔒") # Or Slash Eye
                    else:
                        inp.setEchoMode(QLineEdit.EchoMode.Password)
                        toggle_btn.setText("👁")
                
                toggle_btn.clicked.connect(toggle_password)
                group_layout.addWidget(toggle_btn)
            
            return group, inp

        # Username Group
        self.user_group, self.username_input = create_input_group("Username", "Enter username")
        form_layout.addWidget(self.user_group)
        
        # Password Group
        self.pass_group, self.password_input = create_input_group("Password", "Enter password", is_password=True)
        self.password_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.pass_group)
        
        container_layout.addLayout(form_layout)
        
        # Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border-radius: 8px; 
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
                padding-top: 14px; /* Click effect */
                padding-bottom: 10px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
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
            
        # Loading State
        self.login_btn.setText("Loading...")
        self.login_btn.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        QApplication.processEvents() # Force UI update
        
        # Artificial delay for UX (optional, but requested "loading..")
        # import time; time.sleep(0.5) 
        
        try:
            session = get_db_session()
            user = UserService.authenticate(session, username, password)
            
            if user:
                self.open_dashboard(user)
            else:
                QMessageBox.critical(self, "Login Failed", "Invalid username or password")
                self.reset_ui()
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Login Error: {str(e)}")
             self.reset_ui()

    def reset_ui(self):
        self.login_btn.setText("Login")
        self.login_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
            
    def open_dashboard(self, user):
        from .dashboard import AdminDashboard
        dashboard = AdminDashboard(self.main_window, user)
        self.main_window.switch_to_dashboard(dashboard)
