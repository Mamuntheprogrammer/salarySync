from ui.btn_styles import btn_primary, btn_neutral
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QGridLayout, QPushButton, QSizePolicy, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

from database import get_db_session
from models import Employee, Attendance, ShortLeave, LeaveRequest, Company, BusinessArea, PayrollRecord
from datetime import date, timedelta, datetime
import calendar


# ─────────────────────────────────────────────────────────────────────────────
# KPI Card
# ─────────────────────────────────────────────────────────────────────────────
class KpiCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str, bg: str, icon: str):
        super().__init__()
        self.setObjectName("KpiCard")
        self.setStyleSheet(f"""
            #KpiCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg}, stop:1 {bg}dd);
                border-radius: 12px;
            }}
        """)
        self.setMinimumSize(140, 110)
        self.setMaximumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(4)

        top = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24px; background: transparent; color: white;")
        top.addWidget(lbl_icon)
        top.addStretch()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.80); font-weight: 600; background: transparent;")
        lbl_title.setWordWrap(True)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(lbl_title)
        root.addLayout(top)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("font-size: 30px; font-weight: 800; color: white; background: transparent;")
        root.addWidget(self.lbl_value)

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.70); background: transparent;")
        root.addWidget(self.lbl_sub)

    def update(self, value: str, subtitle: str = None):
        self.lbl_value.setText(value)
        if subtitle is not None:
            self.lbl_sub.setText(subtitle)


# ─────────────────────────────────────────────────────────────────────────────
# Section header
# ─────────────────────────────────────────────────────────────────────────────
def _section_header(title: str, action_text: str = None, action_fn=None) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size:14px; font-weight:700; color:#1a237e;")
    row.addWidget(lbl)
    row.addStretch()
    if action_text and action_fn:
        btn = QPushButton(action_text)
        btn.setStyleSheet(
            "QPushButton{background:transparent;color:#2196F3;border:none;font-size:11px;font-weight:600;}"
            "QPushButton:hover{color:#1565C0;}"
        )
        btn.clicked.connect(action_fn)
        row.addWidget(btn)
    return w


def _card(parent_layout, *, stretch=None):
    """Returns a QFrame styled as a rounded white card."""
    f = QFrame()
    f.setStyleSheet("""
        QFrame {
            background: white;
            border-radius: 10px;
            border: 1px solid #e8eaf6;
        }
    """)
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    if stretch is not None:
        parent_layout.addWidget(f, stretch)
    else:
        parent_layout.addWidget(f)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Main Dashboard
# ─────────────────────────────────────────────────────────────────────────────
class AnalyticsDashboard(QWidget):

    CARD_PALETTES = [
        ("#1976D2", "#42A5F5"),   # Blue
        ("#388E3C", "#66BB6A"),   # Green
        ("#D32F2F", "#EF5350"),   # Red
        ("#F57C00", "#FFA726"),   # Orange
        ("#7B1FA2", "#AB47BC"),   # Purple
        ("#0288D1", "#29B6F6"),   # Cyan
    ]

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f0f2f8;")
        self._build_ui()
        self.load_data()
        # Auto-refresh every 60 s so "Today" numbers stay live
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.load_data)
        self._timer.start(60_000)

    # ── Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # ── Header bar ──────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        lbl_title = QLabel("HRMS Dashboard")
        lbl_title.setStyleSheet("font-size:20px; font-weight:800; color:#1a237e;")
        hdr.addWidget(lbl_title)
        hdr.addStretch()

        self.lbl_date = QLabel()
        self.lbl_date.setStyleSheet("color:#666; font-size:12px;")
        hdr.addWidget(self.lbl_date)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.setStyleSheet(
            "QPushButton{background:#3F51B5;color:white;border:none;border-radius:6px;"
            "padding:5px 14px;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#283593;}"
        )
        btn_refresh.clicked.connect(self.load_data)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)
        filter_bar.addWidget(QLabel("Company:"))
        self.cmb_company = QComboBox()
        self.cmb_company.setMinimumWidth(160)
        self.cmb_company.currentIndexChanged.connect(self._on_company)
        filter_bar.addWidget(self.cmb_company)

        filter_bar.addWidget(QLabel("Business Area:"))
        self.cmb_ba = QComboBox()
        self.cmb_ba.setMinimumWidth(160)
        self.cmb_ba.currentIndexChanged.connect(self.refresh_data)
        filter_bar.addWidget(self.cmb_ba)
        filter_bar.addStretch()
        root.addLayout(filter_bar)

        # ── Row 1: KPI cards ────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        titles   = ["Total Employees", "Present Today", "Absent Today", "Late Today", "Pending Leaves", "Short Leave"]
        icons    = ["Emp", "In", "Out", "Late", "LV", "SL"]
        subtexts = ["Active headcount", "Clocked in", "Not checked in", "After shift start", "Awaiting approval", "Approved today"]
        self._kpi_cards = []
        for i, (t, ic, sub) in enumerate(zip(titles, icons, subtexts)):
            bg = self.CARD_PALETTES[i][0]
            c = KpiCard(t, "—", sub, bg, ic)
            kpi_row.addWidget(c)
            self._kpi_cards.append(c)
        root.addLayout(kpi_row)

        # ── Row 2: Chart + Recent activity ──────────────────────────────────
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        # Left: Weekly attendance bar chart
        left_card = _card(mid_row, stretch=6)
        left_lay = QVBoxLayout(left_card)
        left_lay.setContentsMargins(14, 12, 14, 10)
        left_lay.addWidget(_section_header("This Week — Daily Attendance"))
        self._fig_week = Figure(figsize=(5, 3), dpi=95, facecolor="none")
        self._canvas_week = FigureCanvas(self._fig_week)
        self._canvas_week.setStyleSheet("background: transparent;")
        left_lay.addWidget(self._canvas_week)

        # Right: Business area breakdown
        right_card = _card(mid_row, stretch=4)
        right_lay = QVBoxLayout(right_card)
        right_lay.setContentsMargins(14, 12, 14, 10)
        right_lay.addWidget(_section_header("Business Area — Today"))
        self._tbl_ba = QTableWidget()
        self._tbl_ba.setColumnCount(4)

        self._tbl_ba.setHorizontalHeaderLabels(["Business Area", "Total", "Present", "Rate"])
        self._tbl_ba.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl_ba.verticalHeader().setDefaultSectionSize(36)
        self._tbl_ba.verticalHeader().hide()
        self._tbl_ba.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_ba.setAlternatingRowColors(True)
        self._tbl_ba.verticalHeader().setVisible(False)
        self._tbl_ba.setStyleSheet("border:none; gridline-color:#f0f0f0;")
        right_lay.addWidget(self._tbl_ba)

        root.addLayout(mid_row)

        # ── Row 3: Recent clock-ins + Pending leaves ─────────────────────────
        bot_row = QHBoxLayout()
        bot_row.setSpacing(14)

        # Recent activity
        act_card = _card(bot_row, stretch=5)
        act_lay = QVBoxLayout(act_card)
        act_lay.setContentsMargins(14, 12, 14, 10)
        act_lay.addWidget(_section_header("Recent Attendance Activity"))
        self._tbl_recent = QTableWidget()
        self._tbl_recent.setColumnCount(4)

        self._tbl_recent.setHorizontalHeaderLabels(["Employee", "Action", "Time", "Business Area"])
        self._tbl_recent.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl_recent.verticalHeader().setDefaultSectionSize(36)
        self._tbl_recent.verticalHeader().hide()
        self._tbl_recent.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_recent.verticalHeader().setVisible(False)
        self._tbl_recent.setAlternatingRowColors(True)
        self._tbl_recent.setStyleSheet("border:none; gridline-color:#f0f0f0;")
        self._tbl_recent.setMaximumHeight(220)
        act_lay.addWidget(self._tbl_recent)

        # Pending leave requests
        lv_card = _card(bot_row, stretch=4)
        lv_lay = QVBoxLayout(lv_card)
        lv_lay.setContentsMargins(14, 12, 14, 10)
        lv_lay.addWidget(_section_header("Pending Leave Requests"))
        self._tbl_leaves = QTableWidget()
        self._tbl_leaves.setColumnCount(4)

        self._tbl_leaves.setHorizontalHeaderLabels(["Employee", "Type", "From", "To"])
        self._tbl_leaves.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl_leaves.verticalHeader().setDefaultSectionSize(36)
        self._tbl_leaves.verticalHeader().hide()
        self._tbl_leaves.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_leaves.verticalHeader().setVisible(False)
        self._tbl_leaves.setAlternatingRowColors(True)
        self._tbl_leaves.setStyleSheet("border:none; gridline-color:#f0f0f0;")
        self._tbl_leaves.setMaximumHeight(220)
        lv_lay.addWidget(self._tbl_leaves)

        # Payroll summary mini card
        pay_card = _card(bot_row, stretch=3)
        pay_lay = QVBoxLayout(pay_card)
        pay_lay.setContentsMargins(14, 12, 14, 10)
        pay_lay.addWidget(_section_header("Last Payroll Run"))
        self._payroll_grid = QGridLayout()
        self._payroll_grid.setSpacing(6)
        pay_lay.addLayout(self._payroll_grid)
        pay_lay.addStretch()

        root.addLayout(bot_row)

    # ── Load / Refresh ─────────────────────────────────────────────────────
    def load_data(self):
        today = date.today()
        self.lbl_date.setText(today.strftime("%A, %d %B %Y"))
        session = get_db_session()

        # Reload company filter
        saved_co = self.cmb_company.currentData()
        self.cmb_company.blockSignals(True)
        self.cmb_company.clear()
        self.cmb_company.addItem("All Companies", None)
        for c in session.query(Company).order_by(Company.name).all():
            self.cmb_company.addItem(c.name, c.id)
        for i in range(self.cmb_company.count()):
            if self.cmb_company.itemData(i) == saved_co:
                self.cmb_company.setCurrentIndex(i)
                break
        self.cmb_company.blockSignals(False)
        self._reload_ba(session)
        self.refresh_data()

    def _reload_ba(self, session=None):
        if session is None:
            session = get_db_session()
        saved = self.cmb_ba.currentData()
        self.cmb_ba.blockSignals(True)
        self.cmb_ba.clear()
        self.cmb_ba.addItem("All Areas", None)
        cid = self.cmb_company.currentData()
        q = session.query(BusinessArea)
        if cid:
            q = q.filter_by(company_id=cid)
        for ba in q.order_by(BusinessArea.name).all():
            self.cmb_ba.addItem(ba.name, ba.id)
        for i in range(self.cmb_ba.count()):
            if self.cmb_ba.itemData(i) == saved:
                self.cmb_ba.setCurrentIndex(i)
                break
        self.cmb_ba.blockSignals(False)

    def _on_company(self):
        self._reload_ba()
        self.refresh_data()

    def refresh_data(self):
        session = get_db_session()
        today = date.today()
        cid = self.cmb_company.currentData()
        ba_id = self.cmb_ba.currentData()

        # Employee base query ─────────────────────────────────────────────
        eq = session.query(Employee).filter_by(is_active=True)
        if cid:   eq = eq.filter_by(company_id=cid)
        if ba_id: eq = eq.filter_by(business_area_id=ba_id)
        employees = eq.all()
        emp_ids   = [e.id for e in employees]
        total_emp = len(emp_ids)

        # Today's attendance ──────────────────────────────────────────────
        today_att = session.query(Attendance).filter(
            Attendance.date == today,
            Attendance.employee_id.in_(emp_ids)
        ).all()
        present_ids = {a.employee_id for a in today_att if a.clock_in}
        present_count = len(present_ids)
        absent_count  = max(0, total_emp - present_count)

        # Late count ──────────────────────────────────────────────────────
        late_count = 0
        for att in today_att:
            if att.clock_in and att.employee and att.employee.shift:
                shift = att.employee.shift
                scheduled_in = datetime.combine(today, shift.start_time)
                allowance_min = shift.late_allowance_minutes or 0
                if att.clock_in > scheduled_in + timedelta(minutes=allowance_min):
                    late_count += 1

        # Pending leave requests ──────────────────────────────────────────
        pending_lv = session.query(LeaveRequest).filter(
            LeaveRequest.status == "Pending",
            LeaveRequest.employee_id.in_(emp_ids)
        ).order_by(LeaveRequest.start_date).all()

        # Short leaves today ──────────────────────────────────────────────
        sl_today = session.query(ShortLeave).filter(
            ShortLeave.date == today,
            ShortLeave.status == "Approved",
            ShortLeave.employee_id.in_(emp_ids)
        ).count()

        # Update KPI cards ────────────────────────────────────────────────
        self._kpi_cards[0].update(str(total_emp))
        self._kpi_cards[1].update(str(present_count),
            f"{int(present_count/total_emp*100) if total_emp else 0}% attendance rate")
        self._kpi_cards[2].update(str(absent_count),
            f"{int(absent_count/total_emp*100) if total_emp else 0}% absent")
        self._kpi_cards[3].update(str(late_count), "Checked in late")
        self._kpi_cards[4].update(str(len(pending_lv)), "Needs approval")
        self._kpi_cards[5].update(str(sl_today), "Approved today")

        # Weekly bar chart ────────────────────────────────────────────────
        self._draw_week_chart(session, emp_ids, today)

        # Business area breakdown ─────────────────────────────────────────
        self._fill_ba_table(session, today, cid)

        # Recent activity ─────────────────────────────────────────────────
        self._fill_recent(session, today, emp_ids)

        # Pending leaves table ────────────────────────────────────────────
        self._fill_leaves(pending_lv)

        # Payroll summary ─────────────────────────────────────────────────
        self._fill_payroll(session, cid)

    # ── Charts ─────────────────────────────────────────────────────────────
    def _draw_week_chart(self, session, emp_ids, today):
        # Build Mon–today (or Mon–Fri)
        week_start = today - timedelta(days=today.weekday())  # Monday
        days = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            if d <= today:
                days.append(d)

        presents, absents, lates = [], [], []
        total = len(emp_ids)
        for d in days:
            att = session.query(Attendance).filter(
                Attendance.date == d,
                Attendance.employee_id.in_(emp_ids)
            ).all()
            p = len({a.employee_id for a in att if a.clock_in})
            late = 0
            for a in att:
                if a.clock_in and a.employee and a.employee.shift:
                    si = datetime.combine(d, a.employee.shift.start_time)
                    if a.clock_in > si + timedelta(minutes=a.employee.shift.late_allowance_minutes or 0):
                        late += 1
            presents.append(p)
            lates.append(late)
            absents.append(max(0, total - p))

        self._fig_week.clear()
        ax = self._fig_week.add_subplot(111)
        ax.set_facecolor("#fafafa")
        self._fig_week.patch.set_alpha(0)

        day_labels = [d.strftime("%a\n%d") for d in days]
        x = range(len(days))
        w = 0.28

        bars_p = ax.bar([i - w for i in x], presents, width=w, color="#4CAF50", label="Present", alpha=0.88)
        bars_a = ax.bar(x, absents,  width=w, color="#EF5350", label="Absent",  alpha=0.88)
        bars_l = ax.bar([i + w for i in x], lates, width=w, color="#FF9800", label="Late", alpha=0.88)

        # Value labels
        for bar in list(bars_p) + list(bars_a) + list(bars_l):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.08, str(int(h)),
                        ha='center', va='bottom', fontsize=7, color="#333")

        # Highlight today
        today_x = today.weekday()
        if today_x < len(days):
            ax.axvspan(today_x - 0.5, today_x + 0.5, color="#E8EAF6", zorder=0, alpha=0.6)
            ax.text(today_x, ax.get_ylim()[1] * 0.97 if ax.get_ylim()[1] > 0 else 0.5,
                    "Today", ha='center', va='top', fontsize=8, color="#3F51B5", fontweight='bold')

        ax.set_xticks(list(x))
        ax.set_xticklabels(day_labels, fontsize=9)
        ax.yaxis.set_major_locator(__import__('matplotlib.ticker', fromlist=['MaxNLocator']).MaxNLocator(integer=True))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylabel("Employees", fontsize=9)
        ax.legend(loc='upper right', fontsize=8, framealpha=0.7)
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        self._fig_week.tight_layout(pad=1.0)
        self._canvas_week.draw()

    # ── Tables ─────────────────────────────────────────────────────────────
    def _fill_ba_table(self, session, today, company_id=None):
        q = session.query(BusinessArea)
        if company_id:
            q = q.filter_by(company_id=company_id)
        areas = q.order_by(BusinessArea.name).all()

        self._tbl_ba.setRowCount(0)
        for row, ba in enumerate(areas):
            total = session.query(Employee).filter_by(
                business_area_id=ba.id, is_active=True
            ).count()
            if total == 0:
                continue
            present = session.query(Attendance).filter(
                Attendance.date == today,
                Attendance.employee_id.in_(
                    [e.id for e in session.query(Employee.id).filter_by(business_area_id=ba.id).all()]
                )
            ).count()
            rate = int(present / total * 100) if total else 0

            self._tbl_ba.insertRow(row)
            self._tbl_ba.setItem(row, 0, QTableWidgetItem(ba.name))
            self._tbl_ba.setItem(row, 1, QTableWidgetItem(str(total)))
            self._tbl_ba.setItem(row, 2, QTableWidgetItem(str(present)))

            rate_item = QTableWidgetItem(f"{rate}%")
            rate_item.setForeground(QColor(
                "#388E3C" if rate >= 80 else "#F57C00" if rate >= 50 else "#D32F2F"
            ))
            rate_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self._tbl_ba.setItem(row, 3, rate_item)

    def _fill_recent(self, session, today, emp_ids):
        # Last 15 attendance events (clock-in or clock-out) today
        records = session.query(Attendance).filter(
            Attendance.date == today,
            Attendance.employee_id.in_(emp_ids)
        ).order_by(Attendance.clock_out.desc().nullslast(), Attendance.clock_in.desc()).limit(15).all()

        self._tbl_recent.setRowCount(0)
        row = 0
        for att in records:
            emp = att.employee
            if not emp: continue
            ba_name = emp.business_area.name if emp.business_area else "—"

            # Clock out
            if att.clock_out:
                self._tbl_recent.insertRow(row)
                self._tbl_recent.setItem(row, 0, QTableWidgetItem(emp.full_name))
                action_item = QTableWidgetItem("[ OUT ]  " + att.clock_out.strftime("%I:%M %p"))
                action_item.setForeground(QColor("#D32F2F"))
                self._tbl_recent.setItem(row, 1, action_item)
                self._tbl_recent.setItem(row, 2, QTableWidgetItem(att.clock_out.strftime("%I:%M %p")))
                self._tbl_recent.setItem(row, 3, QTableWidgetItem(ba_name))
                row += 1

            # Clock in
            if att.clock_in and row < 15:
                self._tbl_recent.insertRow(row)
                self._tbl_recent.setItem(row, 0, QTableWidgetItem(emp.full_name))
                action_item = QTableWidgetItem("[ IN ]   " + att.clock_in.strftime("%I:%M %p"))
                action_item.setForeground(QColor("#388E3C"))
                self._tbl_recent.setItem(row, 1, action_item)
                self._tbl_recent.setItem(row, 2, QTableWidgetItem(att.clock_in.strftime("%I:%M %p")))
                self._tbl_recent.setItem(row, 3, QTableWidgetItem(ba_name))
                row += 1

        if row == 0:
            self._tbl_recent.insertRow(0)
            item = QTableWidgetItem("No attendance records today")
            item.setForeground(QColor("#aaa"))
            self._tbl_recent.setItem(0, 0, item)

    def _fill_leaves(self, pending):
        self._tbl_leaves.setRowCount(0)
        for row, lr in enumerate(pending[:20]):
            self._tbl_leaves.insertRow(row)
            self._tbl_leaves.setItem(row, 0, QTableWidgetItem(lr.employee.full_name if lr.employee else "?"))
            type_item = QTableWidgetItem(lr.leave_type or "—")
            type_item.setForeground(QColor("#7B1FA2"))
            self._tbl_leaves.setItem(row, 1, type_item)
            self._tbl_leaves.setItem(row, 2, QTableWidgetItem(lr.start_date.strftime("%d %b") if lr.start_date else "—"))
            self._tbl_leaves.setItem(row, 3, QTableWidgetItem(lr.end_date.strftime("%d %b") if lr.end_date else "—"))
        if not pending:
            self._tbl_leaves.insertRow(0)
            item = QTableWidgetItem("No pending leave requests")
            item.setForeground(QColor("#388E3C"))
            self._tbl_leaves.setItem(0, 0, item)

    def _fill_payroll(self, session, company_id=None):
        # Clear grid
        while self._payroll_grid.count():
            w = self._payroll_grid.takeAt(0).widget()
            if w: w.deleteLater()

        # Last payroll run
        q = session.query(PayrollRecord).order_by(
            PayrollRecord.year.desc(), PayrollRecord.month.desc()
        )
        last = q.first()

        def _row(label, val, color="#333"):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:11px; color:#666;")
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(f"font-size:13px; font-weight:700; color:{color};")
            return lbl, val_lbl

        if not last:
            lbl = QLabel("No payroll records found.")
            lbl.setStyleSheet("color:#aaa; font-size:12px;")
            self._payroll_grid.addWidget(lbl, 0, 0, 1, 2)
            return

        month_str = datetime(last.year, last.month, 1).strftime("%B %Y")
        count = q.filter_by(year=last.year, month=last.month).count()
        total_net = sum(p.net_salary for p in q.filter_by(year=last.year, month=last.month).all())

        rows = [
            ("Period",        month_str,                   "#1976D2"),
            ("Employees Paid", str(count),                 "#333"),
            ("Total OT Hrs",  f"{last.ot_hours:.1f} h",   "#F57C00"),
            ("Total Net Pay", f"৳ {total_net:,.0f}",      "#388E3C"),
        ]
        for r, (label, val, color) in enumerate(rows):
            l, v = _row(label, val, color)
            self._payroll_grid.addWidget(l, r, 0)
            self._payroll_grid.addWidget(v, r, 1)
