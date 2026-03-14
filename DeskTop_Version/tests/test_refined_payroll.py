from database import get_db_session
from services.payroll_service import PayrollService
from services.shift_service import ShiftService
from models import Employee
from datetime import date, datetime, timedelta

def test_refinement():
    session = get_db_session()
    emp = session.query(Employee).filter_by(emp_code='500001').first()
    
    today = date.today()
    month = today.month
    year = today.year
    
    print(f"Testing Refined Payroll for {emp.full_name}")
    
    # Check Shift Duration
    shift_details = ShiftService.get_employee_shift_details(emp)
    if shift_details:
        s_start = datetime.combine(date.min, shift_details["start_time"])
        s_end = datetime.combine(date.min, shift_details["end_time"])
        if s_end < s_start: s_end += timedelta(days=1)
        dur = (s_end - s_start).total_seconds() / 3600.0
        print(f"Detected Shift Duration: {dur} hours")
    else:
        print("No shift found (using default 8h?)")

    result = PayrollService.calculate_salary(session, emp.id, month, year)
    print("-" * 30)
    print(f"Total Work Hours (Decimal): {result['total_work_hours']}")
    
    # Simulate UI Formatting
    wh_val = result["total_work_hours"]
    hours = int(wh_val)
    minutes = int((wh_val - hours) * 60)
    print(f"Formatted Work Hours: {hours}:{minutes:02d}")
    
    print(f"Net Salary: {result['net_salary']}")
    print("-" * 30)

if __name__ == "__main__":
    test_refinement()
