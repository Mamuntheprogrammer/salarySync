from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from models import Attendance, Employee, ShortLeave # Removed Holiday
from .shift_service import ShiftService
from .calendar_service import CalendarService
from config import Config

class AttendanceService:
    @staticmethod
    def _resolve_employee(session: Session, code_or_id: str):
        """Look up employee by attendance_code first, then by numeric id."""
        emp = session.query(Employee).filter_by(attendance_code=code_or_id).first()
        if not emp and code_or_id.isdigit():
            emp = session.query(Employee).filter_by(id=int(code_or_id)).first()
        return emp

    @staticmethod
    def clock_in(session: Session, employee_code: str) -> dict:
        employee = AttendanceService._resolve_employee(session, employee_code)
        if not employee:
            return {"success": False, "message": "Invalid Employee Code / ID"}
            
        if not employee.is_active:
             return {"success": False, "message": "Employee is inactive. Contact Admin."}
            
        today = date.today()
        attendance = session.query(Attendance).filter_by(employee_id=employee.id, date=today).first()
        
        if attendance and attendance.clock_in:
             return {"success": False, "message": f"Already Clocked In at {attendance.clock_in.strftime('%H:%M')}"}
             
        if not attendance:
            attendance = Attendance(employee_id=employee.id, date=today)
            session.add(attendance)
            
        attendance.clock_in = datetime.now()
        
        # Calculate stats (Late check)
        AttendanceService.calculate_daily_stats(session, attendance, employee)
        
        session.commit()
        
        return {
            "success": True, 
            "message": f"{employee.full_name} - Check In at {attendance.clock_in.strftime(Config.get_time_fmt())}", 
            "time": attendance.clock_in.strftime(Config.get_time_fmt()),
            "employee_name": employee.full_name
        }

    @staticmethod
    def clock_out(session: Session, employee_code: str) -> dict:
        employee = AttendanceService._resolve_employee(session, employee_code)
        if not employee:
             return {"success": False, "message": "Invalid Employee Code / ID"}
             
        if not employee.is_active:
             return {"success": False, "message": "Employee is inactive. Contact Admin."}
             
        today = date.today()
        attendance = session.query(Attendance).filter_by(employee_id=employee.id, date=today).first()
        
        if not attendance or not attendance.clock_in:
             return {"success": False, "message": "You have not clocked in yet"}
             
        if attendance.clock_out:
             return {"success": False, "message": f"Already Clocked Out at {attendance.clock_out.strftime('%H:%M')}"}
             
        attendance.clock_out = datetime.now()
        
        # Calculate stats immediately upon clock out
        AttendanceService.calculate_daily_stats(session, attendance, employee)
        
        session.commit()
        
        return {
            "success": True, 
            "message": f"{employee.full_name} - Check Out at {attendance.clock_out.strftime(Config.get_time_fmt())}",
            "time": attendance.clock_out.strftime(Config.get_time_fmt()),
             "employee_name": employee.full_name
        }

    @staticmethod
    def record_short_leave(session: Session, employee_code: str, reason: str, start_time: time, end_time: time) -> dict:
        employee = AttendanceService._resolve_employee(session, employee_code)
        if not employee:
             return {"success": False, "message": "Invalid Employee Code / ID"}
             
        if not employee.is_active:
             return {"success": False, "message": "Employee is inactive. Contact Admin."}
             
        leave = ShortLeave(
            employee_id=employee.id,
            date=date.today(),
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            status="Pending"
        )
        session.add(leave)
        session.commit()
        
        # Calculate duration in minutes
        duration = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
        duration_minutes = int(duration.total_seconds() / 60)

        return {
            "success": True, 
            "message": f"{employee.full_name} - Short Leave from {start_time.strftime(Config.get_time_fmt())} to {end_time.strftime(Config.get_time_fmt())} ({duration_minutes} mins)"
        }

    @staticmethod
    def calculate_daily_stats(session: Session, attendance: Attendance, employee: Employee = None):
        if not employee:
            employee = attendance.employee
        shift = ShiftService.get_employee_shift_details(employee)
        
        # 1. Calculate Short Leave (Approved Only) - Always calculate this
        # ... Short leave logic kept but assignment removed if field gone?
        # User said "remove duty_time_hours, overtime_hours, short_leave_hours" from Attendance table too.
        # Wait, step 0 in my task.md says: Remove `dutytime hour`, `overtime hours`, `shorttime leave hours` from Attendance table.
        # So I should remove those assignments too!
        # The user ONLY asked to remove `late_hours` NOW, but previously asked for the others.
        # I missed cleaning up `attendance_service.py` for those fields earlier!
        # I should clean ALL of them now.
        
        # Checking for Clock In (needed)
        if not attendance.clock_in:
            return

        # 2. Check for Holiday (Simple logic for now)
        hol_info = CalendarService.is_holiday(session, attendance.date, employee)
        if hol_info['is_holiday'] and hol_info['is_ot_eligible']:
            attendance.is_holiday_ot = True
            # No calculated fields to update
            return

        # 3. Standard Day Calculation
        # With all fields removed (duty, ot, short, late), there is literally nothing to calculate here 
        # except maybe validation or future logic.
        # For now, we just pass.
        pass
