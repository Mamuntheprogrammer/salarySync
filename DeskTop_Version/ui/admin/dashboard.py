from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import Config
from services.sync_service import SyncService

class CollapsibleBox(QWidget):
    def __init__(self, title, parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_button = QPushButton(f"▶ {title}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("""
            QPushButton { 
                text-align: left; 
                padding: 10px; 
                background-color: transparent; 
                color: #888; 
                font-weight: bold; 
                text-transform: uppercase; 
                font-size: 11px;
                border: none;
            }
            QPushButton:hover { color: white; background-color: #444; }
            QPushButton:checked { color: white; }
        """)
        self.toggle_button.toggled.connect(self.on_toggled)
        self.toggle_button.setChecked(False)  # Default Collapsed

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setVisible(False)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)
        
    def on_toggled(self, checked):
        text = self.toggle_button.text()
        clean_text = text[2:] if text.startswith(('▼', '▶')) else text
        self.toggle_button.setText(f"{'▼' if checked else '▶'} {clean_text}")
        
        if checked:
            self.content_area.setMaximumHeight(1000) # Arbitrary max
            self.content_area.setVisible(True)
        else:
            self.content_area.setMaximumHeight(0)
            self.content_area.setVisible(False)
            
    def setContentLayout(self, layout):
        self.content_area.setLayout(layout)


class AdminDashboard(QWidget):
    def __init__(self, main_window, user):
        super().__init__()
        self.main_window = main_window
        self.current_user = user
        self.menu_buttons = {}
        self.init_ui()
    
    def check_remote_status(self):
        config = Config.load_config()
        remote_cfg = config.get("remote_db", {})
        
        if remote_cfg.get("enabled") and remote_cfg.get("connection_string"):
            service = SyncService()
            success, _ = service.test_remote_connection(remote_cfg["connection_string"])
            
            if success:
                self.lbl_remote_status.setText("🟢 Online")
                self.lbl_remote_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.lbl_remote_status.setToolTip("Remote DB Connected")
            else:
                self.lbl_remote_status.setText("🔴 Offline")
                self.lbl_remote_status.setStyleSheet("color: #f44336; font-weight: bold;")
                self.lbl_remote_status.setToolTip("Remote DB Connection Failed")
        else:
             self.lbl_remote_status.setText("⚪ Local")
             self.lbl_remote_status.setStyleSheet("color: #aaa;")
             self.lbl_remote_status.setToolTip("Remote DB Not Configured")
             
    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # 1. Sidebar Menu
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #333; color: white;")
        sidebar.setFixedWidth(220) # Slightly wider for indents
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # App Title
        app_title = QLabel(f"AttenSync Admin\n({self.current_user.username})")
        app_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        app_title.setStyleSheet("padding: 20px 0; color: #fff;")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_title)

        self.lbl_remote_status = QLabel("Checking...")
        self.lbl_remote_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.lbl_remote_status)
        
        # Determine Permissions
        allowed_non_admin = ["dashboard", "terminal", "attendance"]
        
        def is_allowed(key):
            if self.current_user.role == "admin": return True
            return key in allowed_non_admin

        # Menu Definition
        groups = {
            "Main": [
                {"label": "Dashboard", "key": "dashboard"},
                {"label": "Attendance Terminal", "key": "terminal"},
                {"label": "Attendance Manager", "key": "attendance"},
                {"label": "Employee Manager", "key": "employees"},
                {"label": "Leave Approval", "key": "leave_approval"},
            ],
            "Reports": [
                {"label": "Summary Report", "key": "reports"},
                # Note: "Month Wise" is a tab inside Reports module, not a separate page key here.
            ],
            "Master Data": [
                {"label": "Import Data", "key": "legacy_import"},
                {"label": "Company Manager", "key": "companies"},
                {"label": "Designation Manager", "key": "designations"},
                {"label": "Shift Manager", "key": "shifts"},
                {"label": "Holiday & Weekly Manager", "key": "calendars"},
                {"label": "Leave Quotas", "key": "leave_quotas"},
                {"label": "Short Leave Manager", "key": "short_leaves"},
            ],
            "System": [
                {"label": "User Manager", "key": "users"},
                {"label": "Payroll Config Manager", "key": "payroll_config"},
                {"label": "Backup & Restore", "key": "backup"},
                {"label": "Run Payroll", "key": "payroll"},
                {"label": "Cloud Sync", "key": "cloud"},
            ]
        }

        # Add Main Items (Flat)
        for item in groups["Main"]:
            if is_allowed(item["key"]):
                self.add_menu_btn(sidebar_layout, item["label"], item["key"])
        
        # Add Collapsible Sections
        for section in ["Reports", "Master Data", "System"]:
            box_items = [i for i in groups[section] if is_allowed(i["key"])]
            
            if box_items:
                box = CollapsibleBox(section)
                box_layout = QVBoxLayout()
                box_layout.setContentsMargins(15, 0, 0, 0)
                box_layout.setSpacing(0)
                
                for item in box_items:
                    self.add_menu_btn(box_layout, item["label"], item["key"])
                
                box.setContentLayout(box_layout)
                sidebar_layout.addWidget(box)

        # Spacer
        sidebar_layout.addStretch()
        
        # Logout
        btn_logout = QPushButton("Logout")
        btn_logout.setStyleSheet("background-color: #f44336; color: white; padding: 10px; border: none;")
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)
        
        layout.addWidget(sidebar)
        
        # 2. Main Content Area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #f5f5f5;")
        layout.addWidget(self.content_area)
        
        # Init Modules
        self.init_modules()
        self.check_remote_status()
        
        if self.pages and "dashboard" in self.menu_buttons:
             self.menu_buttons["dashboard"].click()

    def add_menu_btn(self, layout, label, key):
         btn = QPushButton(label)
         btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left; 
                padding: 8px 10px 8px 10px; 
                padding-left: 10px;
                background-color: transparent; 
                border: none; 
                color: #ddd;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #555;
                color: white;
            }}
            QPushButton:checked {{
                background-color: #2196F3;
                color: white;
            }}
         """)
         btn.setCheckable(True)
         btn.clicked.connect(lambda checked, k=key: self.navigate(k))
         layout.addWidget(btn)
         self.menu_buttons[key] = btn

    def init_modules(self):
        # Create pages
        self.pages = {}
        
        # Dashboard Home
        from .analytics_dashboard import AnalyticsDashboard
        self.pages["dashboard"] = AnalyticsDashboard()
        
        # Admin Terminal
        from .admin_terminal import AdminTerminal
        self.pages["terminal"] = AdminTerminal()
        
        # Companies
        from .company_management import CompanyManagement
        self.pages["companies"] = CompanyManagement()
        
        # Employees
        from .employee_management import EmployeeManagement
        self.pages["employees"] = EmployeeManagement()

        # Shifts
        from .shift_management import ShiftManagement
        self.pages["shifts"] = ShiftManagement()
        
        # Designations
        from .designation_management import DesignationManagement
        self.pages["designations"] = DesignationManagement()
        
        # Attendance
        from .attendance_maintenance import AttendanceMaintenance
        self.pages["attendance"] = AttendanceMaintenance()
        
        # Payroll
        from .payroll_module import PayrollModule
        self.pages["payroll"] = PayrollModule()

        # Leave Approval
        from .leave_approval import LeaveApproval
        self.pages["leave_approval"] = LeaveApproval()

        # Reports
        from .reports import ReportsModule
        self.pages["reports"] = ReportsModule()

        # Legacy Import
        from .legacy_import import LegacyImportModule
        self.pages["legacy_import"] = LegacyImportModule()

        # Calendars
        from .calendar_management import CalendarManagement
        self.pages["calendars"] = CalendarManagement()
        
        # Leave Quotas
        from .leave_quota_management import LeaveQuotaManagement
        self.pages["leave_quotas"] = LeaveQuotaManagement()

        # Short Leaves
        from .short_leave_management import ShortLeaveManagement
        self.pages["short_leaves"] = ShortLeaveManagement()
        
        # Backup
        from .backup_settings import BackupSettings
        self.pages["backup"] = BackupSettings()

        # Cloud Sync
        from ui.setup.cloud_setup import CloudSetup
        self.pages["cloud"] = CloudSetup()

        # Payroll Config
        from .payroll_config_management import PayrollConfigManagement
        self.pages["payroll_config"] = PayrollConfigManagement()
        
        # Users 
        if self.current_user.role == "admin":
             from .user_management import UserManagement
             self.pages["users"] = UserManagement()
        
        for key, widget in self.pages.items():
            self.content_area.addWidget(widget)
            
    def navigate(self, key):
        # Uncheck all others
        for k, btn in self.menu_buttons.items():
            if k != key:
                btn.setChecked(False)
        self.menu_buttons[key].setChecked(True)
        
        # Determine Page
        target_key = key
        mode = None
        if key.startswith("report_"):
            target_key = "reports"
            mode = key
            
        if target_key not in self.pages:
            return

        widget = self.pages[target_key]
        self.content_area.setCurrentWidget(widget)
        
        # Auto-Refresh / Set Mode
        if mode and hasattr(widget, "set_mode"):
            widget.set_mode(mode)
        elif hasattr(widget, "load_data"):
            widget.load_data()
        elif hasattr(widget, "refresh"):
            widget.refresh()
        
    def logout(self):
        self.main_window.logout()
