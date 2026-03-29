from ui.btn_styles import btn_primary, btn_danger, btn_neutral
from ui.page_helpers import make_page_header
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QComboBox, QMessageBox,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.attendance_service import AttendanceService
from database import get_db_session
from models import Company, BusinessArea, Employee
from config import Config


class AdminTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_companies()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Admin Attendance Terminal",
                                          "Manually clock employees in or out from the admin panel"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)

        # ── Employee selection card ──────────────────────────────────────────
        sel_group = QGroupBox("Select Employee")
        sel_grid = QGridLayout(sel_group)
        sel_grid.setContentsMargins(16, 12, 16, 12)
        sel_grid.setSpacing(12)

        sel_grid.addWidget(QLabel("Company:"), 0, 0)
        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(220)
        self.company_combo.currentIndexChanged.connect(self.on_company_change)
        sel_grid.addWidget(self.company_combo, 0, 1)

        sel_grid.addWidget(QLabel("Business Area:"), 1, 0)
        self.ba_combo = QComboBox()
        self.ba_combo.setMinimumWidth(220)
        self.ba_combo.currentIndexChanged.connect(self.on_ba_change)
        sel_grid.addWidget(self.ba_combo, 1, 1)

        sel_grid.addWidget(QLabel("Employee:"), 2, 0)
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumWidth(220)
        self.emp_combo.currentIndexChanged.connect(self.on_emp_change)
        sel_grid.addWidget(self.emp_combo, 2, 1)
        cl.addWidget(sel_group)

        # ── ID input / display ───────────────────────────────────────────────
        id_group = QGroupBox("Employee ID")
        id_layout = QVBoxLayout(id_group)
        id_layout.setContentsMargins(16, 8, 16, 12)

        self.code_display = QLineEdit()
        self.code_display.setPlaceholderText("Enter Employee ID directly or select above")
        self.code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_display.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.code_display.setMinimumHeight(48)
        id_layout.addWidget(self.code_display)
        cl.addWidget(id_group)

        # ── Action buttons ───────────────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.btn_in = QPushButton("🕐  Clock IN")
        self.btn_in.setStyleSheet(btn_primary())
        self.btn_in.setMinimumHeight(44)
        self.btn_in.clicked.connect(self.action_clock_in)

        self.btn_out = QPushButton("🕐  Clock OUT")
        self.btn_out.setStyleSheet(btn_danger())
        self.btn_out.setMinimumHeight(44)
        self.btn_out.clicked.connect(self.action_clock_out)

        self.btn_leave = QPushButton("📋  Leave Request")
        self.btn_leave.setStyleSheet(btn_neutral())
        self.btn_leave.setMinimumHeight(44)
        self.btn_leave.clicked.connect(self.action_leave_request)

        action_row.addWidget(self.btn_in)
        action_row.addWidget(self.btn_out)
        action_row.addWidget(self.btn_leave)
        cl.addLayout(action_row)

        # ── Status feedback ──────────────────────────────────────────────────
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        self.status_label.setMinimumHeight(36)
        cl.addWidget(self.status_label)

        cl.addStretch()
        layout.addWidget(content, stretch=1)

    # ── Data loading ─────────────────────────────────────────────────────────

    def load_companies(self):
        self.company_combo.blockSignals(True)
        self.company_combo.clear()
        self.company_combo.addItem("— Select Company —", None)
        session = get_db_session()
        for c in session.query(Company).all():
            self.company_combo.addItem(f"{c.code} — {c.name}", c.id)
        self.company_combo.blockSignals(False)

    def on_company_change(self):
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("— Select Business Area —", None)
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("— Select Employee —", None)
        self.emp_combo.blockSignals(False)
        self.code_display.clear()

        company_id = self.company_combo.currentData()
        if company_id:
            session = get_db_session()
            for ba in session.query(BusinessArea).filter_by(company_id=company_id).all():
                self.ba_combo.addItem(f"{ba.code} — {ba.name}", ba.id)
        self.ba_combo.blockSignals(False)

    def on_ba_change(self):
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("— Select Employee —", None)
        self.code_display.clear()

        ba_id = self.ba_combo.currentData()
        if ba_id:
            session = get_db_session()
            for emp in session.query(Employee).filter_by(business_area_id=ba_id).all():
                self.emp_combo.addItem(f"{emp.id} — {emp.full_name}", str(emp.id))
        self.emp_combo.blockSignals(False)

    def on_emp_change(self):
        code = self.emp_combo.currentData()
        self.code_display.setText(code if code else "")

    # ── Actions ──────────────────────────────────────────────────────────────

    def get_code(self):
        code = self.code_display.text().strip()
        if not code:
            self._set_status("Please enter or select an Employee ID", success=False)
            return None
        return code

    def action_clock_in(self):
        code = self.get_code()
        if code:
            result = AttendanceService.clock_in(get_db_session(), code)
            self.handle_result(result)

    def action_clock_out(self):
        code = self.get_code()
        if code:
            result = AttendanceService.clock_out(get_db_session(), code)
            self.handle_result(result)

    def action_leave_request(self):
        code = self.get_code()
        if not code:
            return
        session = get_db_session()
        employee = session.query(Employee).filter_by(id=int(code)).first() if code.isdigit() else None
        if not employee:
            self._set_status("Employee not found", success=False)
            return
        from ui.dialogs.leave_request_dialog import LeaveRequestDialog
        LeaveRequestDialog(self, session, employee).exec()

    def handle_result(self, result):
        self._set_status(result['message'], success=result['success'])
        if result['success']:
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def _set_status(self, msg, success=True):
        colour = "#388E3C" if success else "#D32F2F"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(
            f"color: {colour}; font-size: 14px; font-weight: 600; background: transparent;"
        )
