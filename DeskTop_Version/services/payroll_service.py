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
        
        # Fetch Short Leaves for the month
        short_leaves = session.query(ShortLeave).filter(
            ShortLeave.employee_id == employee_id,
            ShortLeave.status == "Approved",
            func.extract('month', ShortLeave.date) == month,
            func.extract('year', ShortLeave.date) == year
        ).all()
        
        sl_map = {}
        for sl in short_leaves:
             d = datetime.combine(date.min, sl.end_time) - datetime.combine(date.min, sl.start_time)
             dur_hours = d.total_seconds() / 3600.0
             sl_map[sl.date] = sl_map.get(sl.date, 0) + dur_hours
        
        present_days = 0
        total_late_hours = 0.0
        total_ot_hours = 0.0
        total_holiday_ot_hours = 0.0
        total_short_leave_hours = 0.0
        
        total_work_hours = 0.0
        late_days_count = 0
        
        from .shift_service import ShiftService
        
        for att in attendance_records:
            # Short Leave
            day_sl_hours = sl_map.get(att.date, 0.0)
            total_short_leave_hours += day_sl_hours
            
            # Check if this day was a holiday?
            if att.is_holiday_ot:
                # If holiday, entire work is OT usually? Or specific field?
                # Assuming 'overtime_hours' meant calculated OT. 
                # Re-calculating OT for holiday:
                if att.clock_in and att.clock_out:
                    dur = (att.clock_out - att.clock_in).total_seconds() / 3600.0
                    total_holiday_ot_hours += dur
            else:
                if att.clock_in: # If clocked in
                     present_days += 1
                
                if att.clock_in and att.clock_out:
                    
                    # Work Hours Calculation
                    raw_work_dur = (att.clock_out - att.clock_in).total_seconds()
                    net_work_dur_sec = max(0, raw_work_dur - (day_sl_hours * 3600))
                    total_work_hours += (net_work_dur_sec / 3600.0)

                    shift = ShiftService.get_employee_shift_details(employee)
                    if shift:
                        # Late
                        sch_in = datetime.combine(att.date, shift["start_time"])
                        if att.clock_in > sch_in:
                            late_diff = (att.clock_in - sch_in).total_seconds()
                            allowance_val = shift.get("late_allowance") or 0
                            allowance_sec = allowance_val * 60
                            
                            if late_diff > allowance_sec:
                                late_days_count += 1
                            
                            if late_diff > 0:
                                total_late_hours += (late_diff / 3600.0)
                        
                        # OT (Duration Based: Net Work - Shift Duration)
                        shift_start = datetime.combine(date.min, shift["start_time"])
                        shift_end = datetime.combine(date.min, shift["end_time"])
                        if shift_end < shift_start:
                             shift_dur = (shift_end - shift_start).total_seconds() + (24*3600)
                        else:
                             shift_dur = (shift_end - shift_start).total_seconds()
                             
                        daily_ot_sec = max(0, net_work_dur_sec - shift_dur)
                        total_ot_hours += (daily_ot_sec / 3600.0)
        
        # 3. Calculate Approved Leave Days (Full Day)
        # absent_days calculation is now just for info, not deduction
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
        # sle_mult = config.short_leave_deduction_multiplier if config else 1.0 # Not used in hourly
        days_in_month_calc = config.days_in_month_calculation if config else 30
        use_actual_days = config.use_actual_days_in_month if config and hasattr(config, 'use_actual_days_in_month') else False
        late_penalty_threshold = config.late_days_penalty_threshold if config and hasattr(config, 'late_days_penalty_threshold') else 0
        
        # Rate Calculation
        divisor = days_in_month_calc
        if use_actual_days:
            try:
                divisor = calendar.monthrange(year, month)[1]
            except:
                pass # default to setting
        
        
        daily_rate = employee.salary_base / divisor
        
        # Calculate Hourly Rate based on Shift Duration
        shift_details = ShiftService.get_employee_shift_details(employee)
        shift_hours = 8.0 # Default
        if shift_details:
             s_start = datetime.combine(date.min, shift_details["start_time"])
             s_end = datetime.combine(date.min, shift_details["end_time"])
             if s_end < s_start:
                 s_end += timedelta(days=1)
             shift_hours = (s_end - s_start).total_seconds() / 3600.0
             
        hourly_rate = daily_rate / shift_hours if shift_hours > 0 else daily_rate / 8
 
        
        # --- CALCULATION (HOURLY BASIS) ---
        
        # Earnings
        work_pay = total_work_hours * hourly_rate
        leave_pay = leaves_on_working_days * 8 * hourly_rate # Assuming 8 hour shift benefit
        
        ot_pay = total_ot_hours * hourly_rate * ot_mult
        holiday_ot_pay = total_holiday_ot_hours * hourly_rate * hot_mult
        
        # Deductions
        late_deduction = total_late_hours * hourly_rate * late_mult
        
        # Late Days Penalty Logic
        late_penalty_deduction = 0.0
        if late_penalty_threshold > 0:
            penalty_days = late_days_count // late_penalty_threshold
            late_penalty_deduction = penalty_days * daily_rate
            
        # Short Leave Deduction - REMOVED (Implicit in work hours)
        short_leave_deduction = 0.0
        
        # Absent Deduction - REMOVED (Implicit in work hours)
        absent_deduction = 0.0
            
        # Net
        # Gross Earned based on hours + leave
        gross_earned = work_pay + leave_pay
        net_salary = gross_earned + ot_pay + holiday_ot_pay - late_deduction - late_penalty_deduction
        
        return {
            "employee_name": employee.full_name,
            "base_salary": round(employee.salary_base, 2),
            "working_days": working_days,
            "present_days": present_days,
            "total_work_hours": round(total_work_hours, 2), # New 
            "absent_days": absent_days,
            "late_hours": round(total_late_hours, 2),
            "late_deduction": round(late_deduction, 2),
            "late_days_penalty": round(late_penalty_deduction, 2),
            "short_leave_hours": round(total_short_leave_hours, 2),
            "short_leave_deduction": 0.0, # Zeroed
            "absent_deduction": 0.0, # Zeroed
            "ot_hours": round(total_ot_hours, 2),
            "ot_pay": round(ot_pay, 2),
            "holiday_ot_hours": round(total_holiday_ot_hours, 2),
            "holiday_ot_pay": round(holiday_ot_pay, 2),
            "net_salary": round(net_salary, 2),
            "divisor_used": divisor
        }
