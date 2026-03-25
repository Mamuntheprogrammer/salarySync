from ui.custom_widgets import make_input_group
from ui.btn_styles import btn_primary, btn_neutral, btn_danger
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDateEdit, 
                             QHeaderView, QComboBox, QMessageBox, QFileDialog, QTabWidget)
from PyQt6.QtCore import QDate, Qt
from database import get_db_session
from models import Attendance, Shift, Employee, ShortLeave, LeaveRequest, Company, BusinessArea, LeaveQuota, Bonus, PayrollRecord, BonusRecord
from services.shift_service import ShiftService
from services.calendar_service import CalendarService
from config import Config
from datetime import timedelta, datetime, time, date
import csv
from sqlalchemy import func

class ReportsModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.tabs = QTabWidget()
        
        # Tab 1: Master Summary
        self.summary_tab = InternalReportWidget(default_mode="report_master_summary")
        self.tabs.addTab(self.summary_tab, "Summary Report")
        
        # Tab 2: Month Wise Attendance
        self.month_wise_tab = InternalReportWidget(default_mode="report_month_wise_attendance")
        self.tabs.addTab(self.month_wise_tab, "Month Wise Attendance")
        
        # Tab 3: Employee Info Report
        self.employee_tab = InternalReportWidget(default_mode="report_employee_info")
        self.tabs.addTab(self.employee_tab, "Employee Report")
        
        # Tab 4: Bonus Report
        self.bonus_tab = InternalReportWidget(default_mode="report_bonus")
        self.tabs.addTab(self.bonus_tab, "Bonus Report")
        
        layout.addWidget(self.tabs)

class InternalReportWidget(QWidget):
    def __init__(self, default_mode="report_master_summary"):
        super().__init__()
        self.mode = default_mode
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header Area
        self.header_layout = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        today = QDate.currentDate()
        month_start = QDate(today.year(), today.month(), 1)
        month_end = QDate(today.year(), today.month(), today.daysInMonth())

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(month_start)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(month_end)
        
        self.header_layout.addWidget(QLabel("From:"))
        self.header_layout.addWidget(self.start_date)
        self.header_layout.addWidget(QLabel("To:"))
        self.header_layout.addWidget(self.end_date)
        
        # Filters
        self.comp_filter = QComboBox()
        self.comp_filter.addItem("All Companies", None)
        self.ba_filter = QComboBox()
        self.ba_filter.addItem("All Business Areas", None)
        self.emp_filter = QComboBox()
        self.emp_filter.addItem("All Employees", None)
        
        self.header_layout.addWidget(QLabel("Comp:"))
        self.header_layout.addWidget(self.comp_filter)
        self.header_layout.addWidget(QLabel("BA:"))
        self.header_layout.addWidget(self.ba_filter)
        self.header_layout.addWidget(QLabel("Emp:"))
        self.header_layout.addWidget(self.emp_filter)
        
        session = get_db_session()
        for c in session.query(Company).all():
             self.comp_filter.addItem(c.name, c.id)
             
        self.comp_filter.currentIndexChanged.connect(self.load_bas)
        self.ba_filter.currentIndexChanged.connect(self.load_emps)
        
        # Initial load of BAs/Emps
        self.load_bas()
        
        btn_generate = QPushButton("Generate")
        btn_generate.setStyleSheet(btn_primary())
        btn_generate.clicked.connect(self.generate_report)
        self.header_layout.addWidget(btn_generate)
        
        btn_export = QPushButton("Export CSV")
        btn_export.setStyleSheet(btn_neutral())
        btn_export.clicked.connect(self.export_csv)
        self.header_layout.addWidget(btn_export)
        
        btn_reset = QPushButton("Reset Filters")
        btn_reset.setStyleSheet(btn_neutral())
        btn_reset.clicked.connect(self.reset_filters)
        self.header_layout.addWidget(btn_reset)
        
        self.header_layout.addStretch()
        layout.addLayout(self.header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        # Header: allow word wrap by fixing height and enabling wrap
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        header.setMinimumSectionSize(80)
        header.setDefaultSectionSize(120)
        header.setMinimumHeight(36)   # Two-line header height, can grow on high-DPI
        self.table.setWordWrap(True)
        layout.addWidget(self.table)
        
        # Initial Setup
        self.setup_table_columns()
        
    def load_bas(self):
        self.ba_filter.blockSignals(True)
        self.ba_filter.clear()
        self.ba_filter.addItem("All Business Areas", None)
        
        session = get_db_session()
        comp_id = self.comp_filter.currentData()
        
        query = session.query(BusinessArea)
        if comp_id:
            query = query.filter_by(company_id=comp_id)
        
        for ba in query.all():
            self.ba_filter.addItem(ba.name, ba.id)
            
        self.ba_filter.blockSignals(False)
        self.load_emps()
        
    def reset_filters(self):
        self.comp_filter.blockSignals(True)
        self.comp_filter.setCurrentIndex(0)
        self.comp_filter.blockSignals(False)
        self.load_bas() # Will cascade reset others
        
        today = QDate.currentDate()
        month_start = QDate(today.year(), today.month(), 1)
        month_end = QDate(today.year(), today.month(), today.daysInMonth())
        
        self.start_date.setDate(month_start)
        self.end_date.setDate(month_end)
        
    def load_emps(self):
        self.emp_filter.blockSignals(True)
        self.emp_filter.clear()
        self.emp_filter.addItem("All Employees", None)
        
        session = get_db_session()
        comp_id = self.comp_filter.currentData()
        ba_id = self.ba_filter.currentData()
        
        query = session.query(Employee).filter_by(is_active=True)
        if comp_id: query = query.filter_by(company_id=comp_id)
        if ba_id: query = query.filter_by(business_area_id=ba_id)
        
        for e in query.all():
            self.emp_filter.addItem(f"{e.id}-{e.full_name}", e.id)
            
        self.emp_filter.blockSignals(False)
        
    def set_mode(self, mode):
        self.mode = mode
        # Title update removed
        self.setup_table_columns()
        self.table.setRowCount(0) # Clear data
        
    def setup_table_columns(self):
        if self.mode == "report_daily":
            cols = ["Date", "Emp ID", "Name", "Shift", "In", "Out", "Status"]
        elif self.mode == "report_monthly":
            cols = ["Emp ID", "Name", "Month", "Present Days"]
        elif self.mode == "report_leave":
            cols = ["Date", "Emp ID", "Name", "Type", "Duration/Reason", "Status"]
        elif self.mode == "report_late":
            cols = [] # Report disabled
        elif self.mode == "report_overtime":
            cols = ["Date", "Emp ID", "Name", "Clock Out", "Shift End", "OT Duration (h)"]
        elif self.mode == "report_master_summary":
            cols = [
                "Emp ID", "Name", "Company", "Business Area", 
                "Total Days", "Working Days", "Present", "Absent", "Late Days",
                "Working (HH:MM)", "Late (HH:MM)", "OT (HH:MM)", "Short Leave (HH:MM)", 
                "Leaves Taken", "Remaining Leave"
            ]
        elif self.mode == "report_month_wise_attendance":
            cols = ["Date", "Emp ID", "Name", "Company", "Business Area", "Shift", "In", "Out", "Status"]
        elif self.mode == "report_employee_info":
            cols = ["Emp ID", "Name", "Company", "Business Area", "Joining Date", "Base Salary", "Valid To", "Resign Status", "Resign Date", "Face Registered?"]
        elif self.mode == "report_bonus":
            cols = ["Period (YY-MM)", "Emp ID", "Name", "Company", "Business Area", "Base Salary", "Bonus Rate/Amt", "Percentage?", "Bonus Payout"]
        elif self.mode == "report_payroll":
            cols = ["Period (YY-MM)", "Emp ID", "Name", "Total Present", "Total Absent", "OT Hrs", "OT Pay", "Late Ded.", "Leave Ded.", "Net Salary"]
        else:
            cols = []
            
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        
    def generate_report(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        session = get_db_session()
        self.current_data = [] # For export
        
        self.table.setRowCount(0)
        
        try:
            if self.mode == "report_daily":
                self.generate_daily(session, start, end)
            elif self.mode == "report_monthly":
                self.generate_monthly(session, start, end)
            elif self.mode == "report_leave":
                self.generate_leave(session, start, end)
            elif self.mode == "report_late":
                self.generate_late(session, start, end)
            elif self.mode == "report_overtime":
                self.generate_overtime(session, start, end)
            elif self.mode == "report_master_summary":
                self.generate_master_summary(session, start, end)
            elif self.mode == "report_month_wise_attendance":
                self.generate_month_wise_attendance(session, start, end)
            elif self.mode == "report_bonus":
                self.generate_bonus_report(session, start, end)
            elif self.mode == "report_employee_info":
                self.generate_employee_info_report(session)
            elif self.mode == "report_payroll":
                self.generate_payroll_report(session, start, end)
                
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "No Data", "No data available for the selected range and filters.")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
            
    def _fmt_duration(self, seconds):
        if not seconds: return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}"

    def generate_daily(self, session, start, end):
        records = session.query(Attendance).filter(Attendance.date >= start, Attendance.date <= end).order_by(Attendance.date).all()
        
        for row, rec in enumerate(records):
            self.table.insertRow(row)
            
            shift_name = rec.employee.shift.name if rec.employee.shift else "Custom"
            in_t = rec.clock_in.strftime("%I:%M %p") if rec.clock_in else "-"
            out_t = rec.clock_out.strftime("%I:%M %p") if rec.clock_out else "-"
            
            status = "Present"
            if not rec.clock_in: status = "Absent?" 
            
            data = [
                rec.date.strftime("%Y-%m-%d"),
                str(rec.employee.id),
                rec.employee.full_name,
                shift_name,
                in_t,
                out_t,
                status
            ]
            self.add_row(row, data)

    def generate_monthly(self, session, start, end):
        stats = session.query(
            Attendance.employee_id,
            func.count(Attendance.id).label('days')
        ).filter(Attendance.date >= start, Attendance.date <= end).group_by(Attendance.employee_id).all()
        
        for row, stat in enumerate(stats):
            self.table.insertRow(row)
            emp = session.query(Employee).get(stat.employee_id)
            month_str = start.strftime("%B %Y")
            
            data = [
                str(emp.id),
                emp.full_name,
                month_str,
                str(stat.days)
            ]
            self.add_row(row, data)

    def generate_leave(self, session, start, end):
        short_leaves = session.query(ShortLeave).filter(ShortLeave.date >= start, ShortLeave.date <= end).all()
        long_leaves = session.query(LeaveRequest).filter(
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start
        ).all()
        
        row_idx = 0
        for l in short_leaves:
            self.table.insertRow(row_idx)
            data = [
                l.date.strftime("%Y-%m-%d"),
                str(l.employee.id),
                l.employee.full_name,
                "Short Leave",
                f"{l.start_time}-{l.end_time} ({l.reason})",
                l.status
            ]
            self.add_row(row_idx, data)
            row_idx += 1
            
        for l in long_leaves:
            self.table.insertRow(row_idx)
            data = [
                f"{l.start_date} to {l.end_date}",
                str(l.employee.id),
                l.employee.full_name,
                l.leave_type,
                l.reason,
                l.status
            ]
            self.add_row(row_idx, data)
            row_idx += 1

    def generate_late(self, session, start, end):
        pass

    def generate_overtime(self, session, start, end):
        records = session.query(Attendance).filter(
            Attendance.date >= start, 
            Attendance.date <= end,
            Attendance.overtime_hours > 0
        ).order_by(Attendance.date).all()
        
        for row, rec in enumerate(records):
            self.table.insertRow(row)
            shift_end = "-"
            if rec.employee.shift:
                shift_end = rec.employee.shift.end_time.strftime("%I:%M %p")
            
            out_t = rec.clock_out.strftime("%I:%M %p") if rec.clock_out else "-"
            
            data = [
                rec.date.strftime("%Y-%m-%d"),
                str(rec.employee.id),
                rec.employee.full_name,
                out_t,
                shift_end,
                str(rec.overtime_hours)
            ]
            self.add_row(row, data)
            
    def generate_master_summary(self, session, start, end):
        query = session.query(Employee).filter_by(is_active=True)
        
        comp_id = self.comp_filter.currentData()
        if comp_id: query = query.filter_by(company_id=comp_id)
        
        ba_id = self.ba_filter.currentData()
        if ba_id: query = query.filter_by(business_area_id=ba_id)
        
        emp_id = self.emp_filter.currentData()
        if emp_id: query = query.filter_by(id=emp_id)
        
        employees = query.all()
        
        for row, emp in enumerate(employees):
            self.table.insertRow(row)
            
            total_days_range = (end - start).days + 1
            
            working_days_count = 0
            curr = start
            while curr <= end:
                is_hol = CalendarService.is_holiday(session, curr, emp)['is_holiday']
                is_weekend = CalendarService.is_weekend(session, curr, emp)
                if not (is_hol or is_weekend):
                    working_days_count += 1
                curr += timedelta(days=1)
                
            att_records = session.query(Attendance).filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= start,
                Attendance.date <= end
            ).all()

            # Fetch Short Leaves for the range first
            sl_records = session.query(ShortLeave).filter(
                ShortLeave.employee_id == emp.id,
                ShortLeave.date >= start,
                ShortLeave.date <= end,
                ShortLeave.status == "Approved"
            ).all()
            
            sl_map = {}
            total_sl_seconds = 0
            for sl in sl_records:
                 d = datetime.combine(date.min, sl.end_time) - datetime.combine(date.min, sl.start_time)
                 dur = d.total_seconds()
                 sl_map[sl.date] = sl_map.get(sl.date, 0) + dur
                 total_sl_seconds += dur

            present_days = 0
            total_work_seconds = 0
            total_late_seconds = 0
            total_ot_seconds = 0
            late_days_count = 0 
            
            for att in att_records:
                if att.clock_in and att.clock_out:
                    present_days += 1
                    raw_work_dur = (att.clock_out - att.clock_in).total_seconds()
                    
                    # Deduct Short Leave for this day from working time
                    day_sl_seconds = sl_map.get(att.date, 0)
                    net_work_dur = str(max(0, raw_work_dur - day_sl_seconds))
                    net_work_dur = float(net_work_dur)
                    
                    total_work_seconds += net_work_dur
                    
                    shift = ShiftService.get_employee_shift_details(emp)
                    if shift:
                        # Late Calculation
                        sch_in = datetime.combine(att.date, shift["start_time"])
                        if att.clock_in > sch_in:
                            late_diff = (att.clock_in - sch_in).total_seconds()
                            allowance_val = shift.get("late_allowance") or 0
                            allowance_sec = allowance_val * 60
                            if late_diff > allowance_sec:
                                late_days_count += 1
                            if late_diff > 0:
                                total_late_seconds += late_diff
                        
                        # OT Calculation (Duration Based: Net Work - Shift Duration)
                        # Calculate Shift Duration
                        shift_start = datetime.combine(date.min, shift["start_time"])
                        shift_end = datetime.combine(date.min, shift["end_time"])
                        if shift_end < shift_start: # Overnight shift handling if needed, though simple subtraction works for duration if on same day. 
                            # Assuming simple day shift or duration calculation:
                            shift_dur = (shift_end - shift_start).total_seconds()
                            if shift_dur < 0: shift_dur += 24*3600 # Wrap around ? Unlikely given models usually
                        else:
                             shift_dur = (shift_end - shift_start).total_seconds()
                             
                        daily_ot = max(0, net_work_dur - shift_dur)
                        total_ot_seconds += daily_ot
            
            absent_days = working_days_count - present_days
            if absent_days < 0: absent_days = 0 
                 
            lr_records = session.query(LeaveRequest).filter(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.status == "Approved",
                LeaveRequest.start_date <= end,
                LeaveRequest.end_date >= start
            ).all()
            
            leaves_taken_days = 0
            for lr in lr_records:
                s = max(lr.start_date, start)
                e = min(lr.end_date, end)
                days = (e - s).days + 1
                if days > 0: leaves_taken_days += days
                
            quotas = session.query(LeaveQuota).filter(
                (LeaveQuota.company_id == emp.company_id) | (LeaveQuota.company_id == None),
                (LeaveQuota.business_area_id == emp.business_area_id) | (LeaveQuota.business_area_id == None)
            ).all()
            
            total_quota = sum([q.quota_limit for q in quotas if q.leave_type != "ShortLeave"])
            remaining = total_quota - leaves_taken_days 
            
            data = [
                str(emp.id),
                emp.full_name,
                emp.company.name if emp.company else "-",
                emp.business_area.name if emp.business_area else "-",
                str(total_days_range),
                str(working_days_count),
                str(present_days),
                str(absent_days),
                str(late_days_count),
                self._fmt_duration(total_work_seconds),
                self._fmt_duration(total_late_seconds),
                self._fmt_duration(total_ot_seconds),
                self._fmt_duration(total_sl_seconds),
                str(leaves_taken_days),
                str(remaining)
            ]
            self.add_row(row, data)

    def add_row(self, row, data):
        self.current_data.append(data)
        for col, val in enumerate(data):
            self.table.setItem(row, col, QTableWidgetItem(str(val)))
            
    def export_csv(self):
        if not hasattr(self, 'current_data') or not self.current_data:
             QMessageBox.warning(self, "Error", "No data to export")
             return
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", f"{self.mode}.csv", "CSV Files (*.csv)")
        if path:
            try:
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(self.current_data)
                QMessageBox.information(self, "Success", "Export Successful")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def generate_month_wise_attendance(self, session, start, end):
        # 1. Identify Employees based on filters
        query = session.query(Employee).filter_by(is_active=True)
        
        comp_id = self.comp_filter.currentData()
        if comp_id: query = query.filter_by(company_id=comp_id)
        
        ba_id = self.ba_filter.currentData()
        if ba_id: query = query.filter_by(business_area_id=ba_id)
        
        emp_id = self.emp_filter.currentData()
        if emp_id: query = query.filter_by(id=emp_id)
        
        employees = query.all()
        
        # 2. Iterate Date Range -> Employees
        row_idx = 0
        for emp in employees:
            curr = start
            while curr <= end:
                self.table.insertRow(row_idx)
                
                # Check Attendance
                att = session.query(Attendance).filter_by(employee_id=emp.id, date=curr).first()
                
                in_t = "-"
                out_t = "-"
                status = "Absent"
                
                # Check Holiday/Weekend
                hol_info = CalendarService.is_holiday(session, curr, emp)
                if hol_info['is_holiday']:
                    status = f"Holiday: {hol_info['description']}"
                elif CalendarService.is_weekend(session, curr, emp):
                    status = "Weekend"
                
                if att:
                    if att.clock_in:
                        in_t = att.clock_in.strftime("%I:%M %p")
                        status = "Present"
                        # Check Late
                        shift = ShiftService.get_employee_shift_details(emp)
                        if shift:
                            sch_in = datetime.combine(curr, shift["start_time"])
                            allowance = shift.get("late_allowance") or 0
                            if att.clock_in > sch_in + timedelta(minutes=allowance):
                                status = "Late"
                                
                    if att.clock_out:
                         out_t = att.clock_out.strftime("%I:%M %p")
                
                # Check Leaves
                lr = session.query(LeaveRequest).filter(
                    LeaveRequest.employee_id == emp.id,
                    LeaveRequest.status == "Approved",
                    LeaveRequest.start_date <= curr,
                    LeaveRequest.end_date >= curr
                ).first()
                if lr:
                    status = f"Leave: {lr.leave_type}"
                    
                shift_name = emp.shift.name if emp.shift else "Custom"
                if emp.shift:
                    s_times = f"{emp.shift.start_time.strftime('%I:%M %p')}-{emp.shift.end_time.strftime('%I:%M %p')}"
                else:
                    s_times = "Custom"
                
                data = [
                    curr.strftime("%Y-%m-%d"),
                    str(emp.id),
                    emp.full_name,
                    emp.company.name if emp.company else "-",
                    emp.business_area.name if emp.business_area else "-",
                    s_times,
                    in_t,
                    out_t,
                    status
                ]
                self.add_row(row_idx, data)
                row_idx += 1
                curr += timedelta(days=1)

        self.add_row(row_idx, data)

    def generate_bonus_report(self, session, start, end):
        # Fetch from BonusRecord snapshot
        start_year, start_month = start.year, start.month
        end_year, end_month = end.year, end.month
        
        all_records = session.query(BonusRecord).order_by(BonusRecord.year.desc(), BonusRecord.month.desc()).all()
        
        row_idx = 0
        for b in all_records:
            b_date = QDate(b.year, b.month, 1).toPyDate()
            
            if start <= b_date <= end:
                emp = b.employee
                
                # Apply filters
                comp_id = self.comp_filter.currentData()
                if comp_id and emp.company_id != comp_id: continue
                ba_id = self.ba_filter.currentData()
                if ba_id and emp.business_area_id != ba_id: continue
                emp_id = self.emp_filter.currentData()
                if emp_id and emp.id != emp_id: continue
                
                self.table.insertRow(row_idx)
                
                period_str = f"{b.year}-{b.month:02d}"
                is_perc = "Yes" if b.is_percentage else "No"
                
                data = [
                    period_str,
                    str(emp.id),
                    emp.full_name,
                    emp.company.name if emp.company else "-",
                    emp.business_area.name if emp.business_area else "-",
                    f"{b.base_salary:.2f}",
                    f"{b.bonus_rate_or_amount:.2f}",
                    is_perc,
                    f"{b.final_bonus_pay:.2f}"
                ]
                self.add_row(row_idx, data)
                row_idx += 1

    def generate_payroll_report(self, session, start, end):
        # Fetch from PayrollRecord snapshot
        all_records = session.query(PayrollRecord).order_by(PayrollRecord.year.desc(), PayrollRecord.month.desc()).all()
        
        row_idx = 0
        for p in all_records:
            p_date = QDate(p.year, p.month, 1).toPyDate()
            if start <= p_date <= end:
                emp = p.employee
                
                # Apply filters
                comp_id = self.comp_filter.currentData()
                if comp_id and emp.company_id != comp_id: continue
                ba_id = self.ba_filter.currentData()
                if ba_id and emp.business_area_id != ba_id: continue
                emp_id = self.emp_filter.currentData()
                if emp_id and emp.id != emp_id: continue
                
                self.table.insertRow(row_idx)
                
                period_str = f"{p.year}-{p.month:02d}"
                
                data = [
                    period_str,
                    str(emp.id),
                    emp.full_name,
                    f"{p.total_present:.1f}",
                    f"{p.total_absent:.1f}",
                    f"{p.ot_hours:.2f}",
                    f"{p.ot_pay:.2f}",
                    f"{p.late_deduction:.2f}",
                    f"{p.leave_deduction:.2f}",
                    f"{p.net_salary:.2f}"
                ]
                self.add_row(row_idx, data)
                row_idx += 1

    def generate_employee_info_report(self, session):
        # 1. Identify Employees based on filters
        query = session.query(Employee).filter_by(is_active=True)
        
        comp_id = self.comp_filter.currentData()
        if comp_id: query = query.filter_by(company_id=comp_id)
        
        ba_id = self.ba_filter.currentData()
        if ba_id: query = query.filter_by(business_area_id=ba_id)
        
        emp_id = self.emp_filter.currentData()
        if emp_id: query = query.filter_by(id=emp_id)
        
        employees = query.all()
        
        for row, emp in enumerate(employees):
            self.table.insertRow(row)
            
            status = "Yes" if emp.face_encoding_path else "No"
            
            data = [
                str(emp.id),
                emp.full_name,
                emp.company.name if emp.company else "-",
                emp.business_area.name if emp.business_area else "-",
                emp.joining_date.strftime("%Y-%m-%d") if emp.joining_date else "-",
                f"{emp.salary_base:.2f}",
                emp.valid_to.strftime("%Y-%m-%d") if emp.valid_to else "-",
                emp.resign_status if emp.resign_status else "-",
                emp.resign_date.strftime("%Y-%m-%d") if emp.resign_date else "-",
                status
            ]
            self.add_row(row, data)