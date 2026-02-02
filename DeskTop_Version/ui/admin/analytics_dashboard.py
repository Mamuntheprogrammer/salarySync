from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QFrame, QGridLayout, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

import matplotlib
matplotlib.use('Qt5Agg') # Or QtAgg, works for PyQt6 usually
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

from database import get_db_session
from models import Employee, Attendance, ShortLeave, Company, BusinessArea
from datetime import date, timedelta, datetime
import calendar

class StatCard(QFrame):
    def __init__(self, title, value, color, icon_text=""):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                color: white;
            }}
        """)
        self.setFixedSize(220, 120)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Arial", 12))
        layout.addWidget(lbl_title)
        
        lbl_value = QLabel(str(value))
        lbl_value.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label = lbl_value
        layout.addWidget(lbl_value)

class AnalyticsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_filters()
        self.refresh_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 1. Filters Bar
        filter_layout = QHBoxLayout()
        
        self.company_combo = QComboBox()
        self.company_combo.addItem("All Companies", None)
        self.company_combo.currentIndexChanged.connect(self.on_company_change)
        
        self.ba_combo = QComboBox()
        self.ba_combo.addItem("All Areas", None)
        self.ba_combo.currentIndexChanged.connect(self.refresh_data)
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_data)
        
        style = """
            QComboBox { padding: 5px; border: 1px solid #ccc; border-radius: 4px; background: white; color: #333; min-width: 150px; }
            QPushButton { padding: 5px 15px; background: #2196F3; color: white; border: none; border-radius: 4px; }
        """
        self.company_combo.setStyleSheet(style)
        self.ba_combo.setStyleSheet(style)
        btn_refresh.setStyleSheet(style)
        
        filter_layout.addWidget(QLabel("<b>Filter:</b>"))
        filter_layout.addWidget(self.company_combo)
        filter_layout.addWidget(self.ba_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_refresh)
        
        layout.addLayout(filter_layout)
        
        # 2. KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        
        self.card_total = StatCard("Total Employees", "0", "#607D8B")
        self.card_present = StatCard("Present Today", "0", "#4CAF50")
        self.card_absent = StatCard("Absent Today", "0", "#F44336")
        self.card_leaves = StatCard("Short Leaves (Today)", "0", "#FF9800")
        
        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_present)
        kpi_layout.addWidget(self.card_absent)
        kpi_layout.addWidget(self.card_leaves)
        kpi_layout.addStretch()
        
        layout.addLayout(kpi_layout)
        
        # 3. Chart
        layout.addWidget(QLabel("<h3>Attendance Trends (Current Month)</h3>"))
        
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def load_filters(self):
        self.company_combo.blockSignals(True)
        session = get_db_session()
        companies = session.query(Company).all()
        for c in companies:
            self.company_combo.addItem(c.name, c.id)
        self.company_combo.blockSignals(False)
        
    def on_company_change(self):
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("All Areas", None)
        
        comp_id = self.company_combo.currentData()
        if comp_id:
            session = get_db_session()
            bas = session.query(BusinessArea).filter_by(company_id=comp_id).all()
            for ba in bas:
                self.ba_combo.addItem(ba.name, ba.id)
        
        self.ba_combo.blockSignals(False)
        self.refresh_data()
        
    def refresh_data(self):
        session = get_db_session()
        today = date.today()
        
        comp_id = self.company_combo.currentData()
        ba_id = self.ba_combo.currentData()
        
        # Base Employee Query
        emp_query = session.query(Employee)
        if comp_id:
            emp_query = emp_query.filter_by(company_id=comp_id)
        if ba_id:
            emp_query = emp_query.filter_by(business_area_id=ba_id)
            
        total_employees = emp_query.count()
        employee_ids = [e.id for e in emp_query.all()]
        
        # Attendance Today
        att_query = session.query(Attendance).filter(
            Attendance.date == today,
            Attendance.employee_id.in_(employee_ids)
        )
        present_count = att_query.count()
        absent_count = max(0, total_employees - present_count)
        
        # Short Leaves Today
        leave_query = session.query(ShortLeave).filter(
            ShortLeave.date == today,
            ShortLeave.employee_id.in_(employee_ids),
            ShortLeave.status == "Approved"
        )
        leave_count = leave_query.count()
        
        # Update Cards
        self.card_total.value_label.setText(str(total_employees))
        self.card_present.value_label.setText(str(present_count))
        self.card_absent.value_label.setText(str(absent_count))
        self.card_leaves.value_label.setText(str(leave_count))
        
        # Update Chart
        self.update_chart(session, employee_ids)
        
    def update_chart(self, session, employee_ids):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Get data for current month
        today = date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        # 1. Fetch Present Counts
        from sqlalchemy import func
        present_results = session.query(Attendance.date, func.count(Attendance.id)).filter(
            Attendance.date >= first_day,
            Attendance.date <= last_day,
            Attendance.employee_id.in_(employee_ids)
        ).group_by(Attendance.date).all()
        present_map = {r[0]: r[1] for r in present_results}
        
        # 2. Fetch Short Leave Counts
        leave_results = session.query(ShortLeave.date, func.count(ShortLeave.id)).filter(
            ShortLeave.date >= first_day,
            ShortLeave.date <= last_day,
            ShortLeave.employee_id.in_(employee_ids),
            ShortLeave.status == "Approved"
        ).group_by(ShortLeave.date).all()
        leave_map = {r[0]: r[1] for r in leave_results}
        
        # 3. Calculate Absent Counts
        # Absent = Total Active Employees - Present
        # (Assuming total employees constant for simplicity for historical data)
        total_employees = len(employee_ids)
        
        dates = []
        present_counts = []
        absent_counts = []
        leave_counts = []
        
        current = first_day
        while current <= last_day:
            if current > today:
                break # Don't plot future dates
                
            dates.append(current)
            p_count = present_map.get(current, 0)
            l_count = leave_map.get(current, 0)
            
            # Simple Absent Calc (ignoring weekends/holidays logic for chart clarity)
            # If strictly 0 present on a weekend, logic might show all absent.
            # Acceptable for MVP dashboard.
            a_count = max(0, total_employees - p_count)
            
            present_counts.append(p_count)
            absent_counts.append(a_count)
            leave_counts.append(l_count)
            
            current += timedelta(days=1)
            
        # Plot Lines
        ax.plot(dates, present_counts, marker='o', linestyle='-', color='#4CAF50', linewidth=2, label='Present')
        ax.plot(dates, absent_counts, marker='o', linestyle='--', color='#F44336', linewidth=2, label='Absent')
        ax.plot(dates, leave_counts, marker='s', linestyle=':', color='#FF9800', linewidth=2, label='Short Leave')
        
        ax.set_title(f"Attendance Trends - {today.strftime('%B %Y')}")
        ax.set_ylabel("Count")
        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Y Axis - Whole Numbers Only
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Format X Axis - Date Wise (Every Day)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1)) # Show every day
        
        # Rotate labels to prevent hiding
        self.figure.autofmt_xdate(rotation=90)
        
        self.figure.tight_layout()
        self.canvas.draw()
