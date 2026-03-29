from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import Config
from services.sync_service import SyncService
from ui import theme


# ─────────────────────────────────────────────────────────────────────────────
# Collapsible sidebar section
# ─────────────────────────────────────────────────────────────────────────────
class CollapsibleBox(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        t = theme.current_palette()
        self.toggle_button = QPushButton(f"  {title}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 9px 12px;
                background-color: transparent;
                color: {t["sidebar_text"]};
                font-weight: 700;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: none;
            }}
            QPushButton:hover {{ color: white; background-color: {t["sidebar_hover"]}; }}
            QPushButton:checked {{ color: white; }}
        """)
        self.toggle_button.toggled.connect(self._toggled)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setVisible(False)
        self.content_area.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

    def _toggled(self, checked):
        txt = self.toggle_button.text().lstrip()
        arrow = "  " if checked else "  "
        self.toggle_button.setText(f"{arrow}{txt}")
        self.content_area.setMaximumHeight(2000 if checked else 0)
        self.content_area.setVisible(checked)

    def setContentLayout(self, layout):
        self.content_area.setLayout(layout)


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard
# ─────────────────────────────────────────────────────────────────────────────
class AdminDashboard(QWidget):
    def __init__(self, main_window, user):
        super().__init__()
        self.main_window = main_window
        self.current_user = user
        self.menu_buttons = {}
        self._build_ui()

    # ── Remote status ───────────────────────────────────────────────────────
    def check_remote_status(self):
        config = Config.load_config()
        remote_cfg = config.get("remote_db", {})
        if remote_cfg.get("enabled") and remote_cfg.get("connection_string"):
            service = SyncService()
            success, _ = service.test_remote_connection(remote_cfg["connection_string"])
            if success:
                self.lbl_remote_status.setText("Online")
                self.lbl_remote_status.setStyleSheet("color: #4CAF50; font-weight: bold; font-size:11px;")
            else:
                self.lbl_remote_status.setText("Offline")
                self.lbl_remote_status.setStyleSheet("color: #f44336; font-weight: bold; font-size:11px;")
        else:
            self.lbl_remote_status.setText("Local")
            self.lbl_remote_status.setStyleSheet("color: #aaa; font-size:11px;")

    # ── Build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        t = theme.current_palette()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar frame ─────────────────────────────────────────────────
        sidebar_frame = QFrame()
        sidebar_frame.setMinimumWidth(210)
        sidebar_frame.setMaximumWidth(260)
        sidebar_frame.setStyleSheet(f"background-color: {t['bg_sidebar']}; border: none;")
        sidebar_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        sidebar_outer = QVBoxLayout(sidebar_frame)
        sidebar_outer.setContentsMargins(0, 0, 0, 0)
        sidebar_outer.setSpacing(0)

        # User info header
        user_banner = QWidget()
        user_banner.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #26324a, stop:1 {t['bg_sidebar']});
            border-bottom: 1px solid rgba(255,255,255,0.08);
        """)
        user_banner.setFixedHeight(80)
        ubl = QVBoxLayout(user_banner)
        ubl.setContentsMargins(16, 10, 16, 10)
        lbl_user = QLabel(self.current_user.username.upper())
        lbl_user.setStyleSheet("color: white; font-size: 14px; font-weight: 800; background: transparent;")
        lbl_role = QLabel(self.current_user.role.capitalize())
        lbl_role.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 11px; background: transparent;")
        ubl.addWidget(lbl_user)
        ubl.addWidget(lbl_role)
        sidebar_outer.addWidget(user_banner)

        # Scrollable menu area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        menu_container = QWidget()
        menu_container.setStyleSheet("background: transparent;")
        self.sidebar_layout = QVBoxLayout(menu_container)
        self.sidebar_layout.setContentsMargins(0, 8, 0, 8)
        self.sidebar_layout.setSpacing(0)

        scroll.setWidget(menu_container)
        sidebar_outer.addWidget(scroll, stretch=1)

        # Remote status + logout at bottom
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet(f"""
            background: rgba(0,0,0,0.25);
            border-top: 1px solid rgba(255,255,255,0.07);
        """)
        bbl = QVBoxLayout(bottom_bar)
        bbl.setContentsMargins(12, 8, 12, 8)
        bbl.setSpacing(6)

        self.lbl_remote_status = QLabel("Checking...")
        self.lbl_remote_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_remote_status.setStyleSheet("color: #aaa; font-size:11px;")
        bbl.addWidget(self.lbl_remote_status)

        btn_logout = QPushButton("Logout")
        btn_logout.setStyleSheet("""
            QPushButton {
                background: #c62828; color: white; border: none;
                border-radius: 5px; padding: 7px; font-weight: 700;
            }
            QPushButton:hover { background: #b71c1c; }
        """)
        btn_logout.clicked.connect(self.logout)
        bbl.addWidget(btn_logout)
        sidebar_outer.addWidget(bottom_bar)

        root.addWidget(sidebar_frame)

        # ── Content area ───────────────────────────────────────────────────
        self.content_area = QStackedWidget()
        t2 = theme.current_palette()
        self.content_area.setStyleSheet(f"QStackedWidget {{ background-color: {t2['bg_main']}; border: none; }}")
        root.addWidget(self.content_area, stretch=1)

        self._populate_menu()
        self.init_modules()
        self.check_remote_status()

        if "dashboard" in self.menu_buttons:
            self.menu_buttons["dashboard"].click()

    # ── Menu population ─────────────────────────────────────────────────────
    def _populate_menu(self):
        allowed_non_admin = ["dashboard", "terminal", "attendance"]

        def is_allowed(key):
            if self.current_user.role == "admin":
                return True
            return key in allowed_non_admin

        groups = {
            "Main": [
                {"label": "Dashboard",           "key": "dashboard"},
                {"label": "Attendance Terminal",  "key": "terminal"},
            ],
            "Workforce": [
                {"label": "Employee Manager",     "key": "employees"},
                {"label": "Attendance Manager",   "key": "attendance"},
                {"label": "Leave Approval",       "key": "leave_approval"},
                {"label": "Short Leave Manager",  "key": "short_leaves"},
            ],
            "Payroll & Bonus": [
                {"label": "Payroll Settings",     "key": "payroll_config"},
                {"label": "Bonus Manager",        "key": "bonuses"},
                {"label": "Salary Breakdowns",    "key": "salary_breakdowns"},
                {"label": "Run Payroll",          "key": "payroll"},
                {"label": "Run Bonus",            "key": "bonus_run"},
                {"label": "Print Documents",      "key": "print_documents"},
            ],
            "Organization": [
                {"label": "Company Manager",      "key": "companies"},
                {"label": "Business Area Manager","key": "business_areas"},
                {"label": "Designation Manager",  "key": "designations"},
                {"label": "Shift Manager",        "key": "shifts"},
                {"label": "Holiday & Weekly Off", "key": "calendars"},
                {"label": "Face Manager",         "key": "face_manager"},
                {"label": "Leave Quotas",         "key": "leave_quotas"},
            ],
            "Reports": [
                {"label": "System Reports",       "key": "reports"},
            ],
            "System": [
                {"label": "User Manager",         "key": "users"},
                {"label": "System Logs",          "key": "system_logs"},
                {"label": "Import Data",          "key": "legacy_import"},
                {"label": "Backup & Restore",     "key": "backup"},
                {"label": "Cloud Sync",           "key": "cloud"},
            ],
        }


        # Flat main items
        for item in groups["Main"]:
            if is_allowed(item["key"]):
                self._add_menu_btn(self.sidebar_layout, item["label"], item["key"], flat=True)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.07); margin: 4px 0;")
        self.sidebar_layout.addWidget(div)

        # Collapsible sections
        self.collapsible_boxes = []
        for section in ["Workforce", "Payroll & Bonus", "Organization", "Reports", "System"]:
            items = [i for i in groups[section] if is_allowed(i["key"])]
            if not items:
                continue
            box = CollapsibleBox(section)
            self.collapsible_boxes.append(box)
            box.toggle_button.toggled.connect(lambda checked, b=box: self._on_box_toggled(checked, b))
            box_lay = QVBoxLayout()
            box_lay.setContentsMargins(12, 0, 0, 0)
            box_lay.setSpacing(0)
            for item in items:
                self._add_menu_btn(box_lay, item["label"], item["key"])
            box.setContentLayout(box_lay)
            self.sidebar_layout.addWidget(box)

        self.sidebar_layout.addStretch()

    def _on_box_toggled(self, checked, box):
        if not checked:
            return
        for other_box in self.collapsible_boxes:
            if other_box != box and other_box.toggle_button.isChecked():
                other_box.toggle_button.setChecked(False)

    def _add_menu_btn(self, layout, label, key, flat=False):
        t = theme.current_palette()
        btn = QPushButton(f"  {label}")
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: {"10px 12px" if flat else "8px 12px"};
                background-color: transparent;
                border: none;
                color: {t["sidebar_text"]};
                font-size: {"13px" if flat else "12px"};
                font-weight: {"700" if flat else "400"};
                border-left: 3px solid transparent;
            }}
            QPushButton:hover {{
                background-color: {t["sidebar_hover"]};
                color: white;
                border-left: 3px solid rgba(255,255,255,0.3);
            }}
            QPushButton:checked {{
                background-color: rgba(33,150,243,0.18);
                color: white;
                border-left: 3px solid {t["sidebar_active"]};
                font-weight: 700;
            }}
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked, k=key: self.navigate(k))
        layout.addWidget(btn)
        self.menu_buttons[key] = btn

    # ── Navigation ──────────────────────────────────────────────────────────
    def navigate(self, key):
        for k, btn in self.menu_buttons.items():
            if k != key:
                btn.setChecked(False)
        if key in self.menu_buttons:
            self.menu_buttons[key].setChecked(True)

        target_key = key
        mode = None
        if key.startswith("report_"):
            target_key = "reports"
            mode = key

        if target_key not in self.pages:
            return

        widget = self.pages[target_key]
        self.content_area.setCurrentWidget(widget)

        if mode and hasattr(widget, "set_mode"):
            widget.set_mode(mode)
        elif hasattr(widget, "load_data"):
            widget.load_data()
        elif hasattr(widget, "refresh_data"):
            widget.refresh_data()
        elif hasattr(widget, "refresh"):
            widget.refresh()

    def apply_theme(self):
        """Called by TopBar when theme is toggled."""
        t = theme.current_palette()
        self.content_area.setStyleSheet(f"background-color: {t['bg_main']}; border: none;")

    # ── Module init ─────────────────────────────────────────────────────────
    def init_modules(self):
        self.pages = {}

        from .analytics_dashboard import AnalyticsDashboard
        self.pages["dashboard"] = AnalyticsDashboard()

        from .admin_terminal import AdminTerminal
        self.pages["terminal"] = AdminTerminal()

        from .company_management import CompanyManagement
        self.pages["companies"] = CompanyManagement()

        from .business_area_management import BusinessAreaManagement
        self.pages["business_areas"] = BusinessAreaManagement()

        from .employee_management import EmployeeManagement
        self.pages["employees"] = EmployeeManagement()

        from .shift_management import ShiftManagement
        self.pages["shifts"] = ShiftManagement()

        from .designation_management import DesignationManagement
        self.pages["designations"] = DesignationManagement()

        from .attendance_maintenance import AttendanceMaintenance
        self.pages["attendance"] = AttendanceMaintenance()

        from .payroll_module import PayrollModule
        self.pages["payroll"] = PayrollModule()

        from .bonus_run_module import BonusRunModule
        self.pages["bonus_run"] = BonusRunModule()

        from .leave_approval import LeaveApproval
        self.pages["leave_approval"] = LeaveApproval()

        from .reports import ReportsModule
        self.pages["reports"] = ReportsModule()

        from .legacy_import import LegacyImportModule
        self.pages["legacy_import"] = LegacyImportModule()

        from .calendar_management import CalendarManagement
        self.pages["calendars"] = CalendarManagement()

        from .face_manager import FaceManager
        self.pages["face_manager"] = FaceManager()

        from .leave_quota_management import LeaveQuotaManagement
        self.pages["leave_quotas"] = LeaveQuotaManagement()

        from .short_leave_management import ShortLeaveManagement
        self.pages["short_leaves"] = ShortLeaveManagement()

        from .bonus_management import BonusManagement
        self.pages["bonuses"] = BonusManagement()

        from .salary_breakdown_manager import SalaryBreakdownManager
        self.pages["salary_breakdowns"] = SalaryBreakdownManager()

        from .backup_settings import BackupSettings
        self.pages["backup"] = BackupSettings()

        from ui.setup.cloud_setup import CloudSetup
        self.pages["cloud"] = CloudSetup()

        from .payroll_config_management import PayrollConfigManagement
        self.pages["payroll_config"] = PayrollConfigManagement()

        from .system_logs_manager import SystemLogsManager
        self.pages["system_logs"] = SystemLogsManager()

        from .print_documents import PrintDocumentsModule
        self.pages["print_documents"] = PrintDocumentsModule(self.current_user.username)

        if self.current_user.role == "admin":
            from .user_management import UserManagement
            self.pages["users"] = UserManagement()

        for widget in self.pages.values():
            self.content_area.addWidget(widget)

    # ── Logout ───────────────────────────────────────────────────────────────
    def logout(self):
        self.main_window.logout()
