from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QFrame, QApplication, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from database import get_db_session
from services.user_service import UserService
from config import Config
from services.sync_service import SyncService
from ui.btn_styles import btn_neutral, btn_primary
from ui.page_helpers import style_dialog
from ui import theme
from utils.user_context import set_current_user_id


class AdminLoginWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        t = theme.current_palette()
        self.setStyleSheet(f"background-color: {t['bg_main']};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # ── Login Card ────────────────────────────────────────────────────
        container = QFrame()
        container.setFixedWidth(420)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {t["bg_card"]};
                border-radius: 10px;
                border: 1px solid {t["border"]};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 28))
        container.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(20)

        # Brand header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_lbl = QLabel("AttenSync")
        brand_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        brand_lbl.setStyleSheet(f"color: {t['accent']}; background: transparent; border: none;")
        brand_row.addStretch()
        brand_row.addWidget(brand_lbl)
        brand_row.addStretch()
        card_layout.addLayout(brand_row)

        sub_lbl = QLabel("Admin Portal")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(f"color: {t['text_secondary']}; font-size: 13px; background: transparent; border: none;")
        card_layout.addWidget(sub_lbl)

        # Accent divider
        div = QFrame()
        div.setFixedHeight(2)
        div.setStyleSheet(f"background: {t['accent']}; border: none;")
        card_layout.addWidget(div)

        # Fields
        fields_layout = QVBoxLayout()
        fields_layout.setContentsMargins(10, 10, 10, 10)
        fields_layout.setSpacing(18)

        self.username_input = self._make_field("Username", "Enter username")
        self.password_input = self._make_field("Password", "Enter password", is_password=True)
        fields_layout.addWidget(self._labeled_field("Username", self.username_input))
        fields_layout.addWidget(self._labeled_field("Password", self.password_input))
        self.password_input.returnPressed.connect(self.handle_login)
        card_layout.addLayout(fields_layout)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setStyleSheet(btn_neutral())
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.go_back)
        btn_row.addWidget(self.back_btn, stretch=1)

        self.login_btn = QPushButton("Login")
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        from ui.btn_styles import btn_primary
        self.login_btn.setStyleSheet(btn_primary())
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.handle_login)
        btn_row.addWidget(self.login_btn, stretch=1)

        card_layout.addLayout(btn_row)
        layout.addWidget(container)

        # Remote DB Status
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px; background: transparent;")
        layout.addWidget(self.status_lbl)

        self.ensure_default_admin()
        self.check_remote_status()

    def showEvent(self, event):
        super().showEvent(event)
        # Let Qt process the event frame, then yank focus to the username input
        self.username_input.setFocus()

    def _make_field(self, name: str, placeholder: str, is_password: bool = False) -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setObjectName(name)
        if is_password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        return inp

    def _labeled_field(self, label_text: str, field: QLineEdit) -> QWidget:
        t = theme.current_palette()
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(wrapper)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        vlay.addWidget(lbl)

        if field.echoMode() == QLineEdit.EchoMode.Password:
            # Create a faux input container to fuse field and button
            input_container = QFrame()
            input_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {t['input_bg']};
                    border: 1px solid {t['input_border']};
                    border-radius: 6px;
                }}
            """)
            input_layout = QHBoxLayout(input_container)
            input_layout.setContentsMargins(0, 0, 0, 0)
            input_layout.setSpacing(0)

            # Strip native field borders so it visually merges with container
            field.setStyleSheet("""
                QLineEdit { border: none; background: transparent; padding: 6px 10px; min-height: 30px;}
                QLineEdit:focus { border: none; background: transparent; }
            """)
            input_layout.addWidget(field, stretch=1)

            toggle_btn = QPushButton("👁")
            toggle_btn.setFixedWidth(40)
            toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            # Fallback to Segoe UI emoji or standard default if desired
            toggle_btn.setFont(QFont("Segoe UI Emoji", 14) if "Segoe UI" in QFont().family() else QFont("Arial", 14))
            toggle_btn.setToolTip("Show/Hide Password")
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    background-color: transparent;
                    color: {t['text_muted']};
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }}
                QPushButton:hover {{
                    color: {t['text_primary']};
                    background-color: {t['header_bg']};
                }}
            """)
            def _toggle(*args, btn=toggle_btn, f=field):
                if f.echoMode() == QLineEdit.EchoMode.Password:
                    f.setEchoMode(QLineEdit.EchoMode.Normal)
                    btn.setText("🔒")
                else:
                    f.setEchoMode(QLineEdit.EchoMode.Password)
                    btn.setText("👁")
            toggle_btn.clicked.connect(_toggle)
            
            input_layout.addWidget(toggle_btn)
            vlay.addWidget(input_container)
        else:
            vlay.addWidget(field)

        return wrapper

    def go_back(self):
        if hasattr(self.main_window, 'logout'):
            self.main_window.logout()

    def check_remote_status(self):
        config = Config.load_config()
        remote_cfg = config.get("remote_db", {})
        
        # We check "online_mode" from global config
        is_online = config.get("online_mode", False)
        
        if is_online and remote_cfg.get("connection_string"):
            service = SyncService()
            success, _ = service.test_remote_connection(remote_cfg["connection_string"])
            if success:
                self.status_lbl.setText("🟢 Remote DB Connected")
                self.status_lbl.setStyleSheet("color: #388E3C; font-size: 11px; font-weight: 600; background: transparent;")
            else:
                self.status_lbl.setText("🔴 Remote DB Disconnected")
                self.status_lbl.setStyleSheet("color: #D32F2F; font-size: 11px; font-weight: 600; background: transparent;")
        else:
            self.status_lbl.setText("⚪ Local Mode (Offline)")
            self.status_lbl.setStyleSheet("color: #9999bb; font-size: 11px; background: transparent;")

    def ensure_default_admin(self):
        session = get_db_session()
        if not UserService.get_all_users(session):
            UserService.create_user(session, "admin", "admin123", "admin")
            print("Default admin created: admin / admin123")

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_msg("Login Failed", "Please enter username and password", QMessageBox.Icon.Warning)
            return

        self.login_btn.setText("Verifying...")
        self.login_btn.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        QApplication.processEvents()

        try:
            session = get_db_session()
            user = UserService.authenticate(session, username, password)
            if user:
                self.open_dashboard(user)
            else:
                self._show_msg("Login Failed", "Invalid username or password", QMessageBox.Icon.Critical)
                self.reset_ui()
        except Exception as e:
            self._show_msg("Error", f"Login Error: {str(e)}", QMessageBox.Icon.Critical)
            self.reset_ui()

    def _show_msg(self, title, text, icon):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        style_dialog(msg, min_width=350)
        
        # Force Qt to instantiate the default OK button before we try to style it
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Explicitly style internal message box buttons
        for btn in msg.buttons():
            btn.setStyleSheet(btn_primary())
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setMinimumHeight(32)
            btn.setMinimumWidth(80)
            
        msg.exec()

    def reset_ui(self):
        self.login_btn.setText("Login")
        self.login_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)

    def open_dashboard(self, user):
        from .dashboard import AdminDashboard
        set_current_user_id(user.id)
        dashboard = AdminDashboard(self.main_window, user)
        self.main_window.switch_to_dashboard(dashboard)
