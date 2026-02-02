from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Employee, Attendance, PayrollConfig, ShortLeave, LeaveRequest
from config import Config
from datetime import datetime, date, timedelta
import calendar
from .calendar_service import CalendarService
from .leave_service import LeaveService

class PayrollService:
    @staticmethod
    def calculate_salary(session: Session, employee_id: int, month: int, year: int) -> dict:
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee or not employee.is_active:
             return None
             
        # Range for the month
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # 1. Get Calendar Stats (Working Days, Holidays, Weekends)
        cal_stats = CalendarService.get_month_stats(session, month, year, employee)
        working_days = cal_stats['working_days']
        
        # 2. Get Attendance Stats
        attendance_records = session.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            func.extract('month', Attendance.date) == month,
            func.extract('year', Attendance.date) == year
        ).all()
        
        present_days = 0
        total_late_hours = 0.0
        total_ot_hours = 0.0
        total_holiday_ot_hours = 0.0
        total_short_leave_hours = 0.0
        
        for att in attendance_records:
            total_short_leave_hours += att.short_leave_hours
            
            # Check if this day was a holiday?
            if att.is_holiday_ot:
                total_holiday_ot_hours += att.overtime_hours
            else:
                if att.clock_in: # If clocked in
                     present_days += 1
                
                total_late_hours += att.late_hours
                total_ot_hours += att.overtime_hours
        
        # 3. Calculate Approved Leave Days (Full Day)
        absent_days_raw = max(0, working_days - present_days)
        
        approved_leaves = session.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "Approved",
            (func.extract('month', LeaveRequest.start_date) == month) | (func.extract('month', LeaveRequest.end_date) == month)
        ).all()
        
        leaves_on_working_days = 0
        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)
        
        for req in approved_leaves:
            current = req.start_date
            while current <= req.end_date:
                if month_start <= current <= month_end:
                    is_wknd = CalendarService.is_weekend(session, current, employee)
                    hol_info = CalendarService.is_holiday(session, current, employee)
                    if not is_wknd and not hol_info['is_holiday']:
                        leaves_on_working_days += 1
                current += timedelta(days=1)
                
        absent_days = max(0, absent_days_raw - leaves_on_working_days)
        
        # Get Payroll Config
        config = session.query(PayrollConfig).filter_by(company_id=employee.company_id).first()
        
        # Defaults
        ot_mult = config.ot_rate_multiplier if config else 1.5
        hot_mult = config.holiday_ot_rate_multiplier if config else 2.0
        late_mult = config.late_deduction_multiplier if config else 1.0
        sle_mult = config.short_leave_deduction_multiplier if config else 1.0
        days_in_month_calc = config.days_in_month_calculation if config else 30
        
        # Rate Calculation
        daily_rate = employee.salary_base / days_in_month_calc
        hourly_rate = daily_rate / 8 
        
        # --- CALCULATION ---
        gross_salary = employee.salary_base
        
        # Deductions
        late_deduction = total_late_hours * hourly_rate * late_mult
        
        short_leave_deduction = total_short_leave_hours * hourly_rate * sle_mult
        
        absent_deduction = absent_days * daily_rate
        
        # Additions
        ot_pay = total_ot_hours * hourly_rate * ot_mult
        holiday_ot_pay = total_holiday_ot_hours * hourly_rate * hot_mult
        
        # Net
        net_salary = gross_salary - late_deduction - short_leave_deduction - absent_deduction + ot_pay + holiday_ot_pay
        
        return {
            "employee_name": employee.full_name,
            "base_salary": round(employee.salary_base, 2),
            "working_days": working_days,
            "present_days": present_days, 
            "absent_days": absent_days,
            "late_hours": round(total_late_hours, 2),
            "late_deduction": round(late_deduction, 2),
            "short_leave_hours": round(total_short_leave_hours, 2),
            "short_leave_deduction": round(short_leave_deduction, 2),
            "absent_deduction": round(absent_deduction, 2),
            "ot_hours": round(total_ot_hours, 2),
            "ot_pay": round(ot_pay, 2),
            "holiday_ot_hours": round(total_holiday_ot_hours, 2),
            "holiday_ot_pay": round(holiday_ot_pay, 2),
            "net_salary": round(net_salary, 2)
        }
