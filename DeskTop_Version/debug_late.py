from database import get_db_session
from models import Employee, Attendance, Shift
from services.shift_service import ShiftService
from datetime import date, datetime, timedelta

def check_late():
    session = get_db_session()
    # Find employee 500001
    emp = session.query(Employee).filter_by(attendance_code='500001').first()
    if not emp:
        print("Employee 500001 not found")
        return

    today = date.today()
    print(f"Checking for Employee: {emp.full_name} ({emp.attendance_code}) on {today}")

    # Check Attendance
    att = session.query(Attendance).filter_by(employee_id=emp.id, date=today).first()
    if not att:
        print("No attendance found for today")
    else:
        print(f"Clock In: {att.clock_in}")
        print(f"Clock Out: {att.clock_out}")

    # Check Shift
    shift_details = ShiftService.get_employee_shift_details(emp)
    if shift_details:
        print(f"Shift Found: {shift_details.get('name')}")
        print(f"Shift Start: {shift_details.get('start_time')}")
        print(f"Late Allowance (min): {shift_details.get('late_allowance_minutes')}")
        
        if att and att.clock_in:
            sch_in = datetime.combine(today, shift_details["start_time"])
            allowance = shift_details.get("late_allowance_minutes", 15)
            allowance_delta = timedelta(minutes=allowance)
            limit = sch_in + allowance_delta
            
            print(f"Scheduled In: {sch_in}")
            print(f"Late Threshold: {limit}")
            
            if att.clock_in > limit:
                print("RESULT: Should be LATE")
                diff = (att.clock_in - sch_in).total_seconds()
                print(f"Late seconds: {diff}")
            else:
                print("RESULT: NOT Late (within allowance or early)")
    else:
        print("No Shift Details found")

if __name__ == "__main__":
    check_late()
