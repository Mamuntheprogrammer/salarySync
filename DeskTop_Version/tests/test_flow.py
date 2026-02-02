import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from services.employee_service import EmployeeService
from services.shift_service import ShiftService
from services.attendance_service import AttendanceService
from services.payroll_service import PayrollService
from models import Company, BusinessArea, Shift, Employee, Attendance
from datetime import datetime, time, date

def run_test():
    print("--- Starting End-to-End Simulation ---")
    
    # 1. Initialize DB (In Memory for test or file)
    # Using file to verify persistence if needed, but here just testing logic
    db.initialize()
    session = get_db_session()
    
    # Clean up previous data
    session.query(Attendance).delete()
    session.query(Employee).delete()
    session.query(BusinessArea).delete()
    session.query(Company).delete()
    session.query(Shift).delete()
    session.commit()
    print("[OK] Database Initialized & Cleaned")
    
    # 2. Create Company & Business Area
    company = Company(code="999", name="Test Corp")
    session.add(company)
    session.commit()
    
    ba = BusinessArea(code="01", name="HQ", company_id=company.id)
    session.add(ba)
    session.commit()
    print(f"[OK] Company Created: {company.name} ({company.code})")
    
    # 3. Create Shift
    shift = ShiftService.create_shift(session, "General Shift", time(9,0), time(17,0), 15)
    print(f"[OK] Shift Created: {shift.name}")
    
    # 4. Create Employee
    emp_data = {
        "full_name": "Test User",
        "company_id": company.id,
        "business_area_id": ba.id,
        "salary_base": 60000,
        "shift_id": shift.id
    }
    employee = EmployeeService.create_employee(session, emp_data)
    print(f"[OK] Employee Created: {employee.full_name} (Code: {employee.attendance_code})")
    
    # 5. Simulate Attendance
    # Clock In (On time)
    # Mocking datetime.now() is hard directly, so we rely on the service using real time
    # Or we modify the record manually after creation to simulate past events
    
    res_in = AttendanceService.clock_in(session, employee.attendance_code)
    print(f"[Attendance] Clock In: {res_in['message']}")
    
    if not res_in['success']:
        print("Clock In Failed!")
        return

    # Simulate working time passing... we will manually update the clock_in to 4 hours ago
    rec = session.query(Attendance).filter_by(employee_id=employee.id, date=date.today()).first()
    rec.clock_in = datetime.combine(date.today(), time(9, 5)) # 9:05 AM (Not late)
    session.commit()
    
    # Clock Out
    res_out = AttendanceService.clock_out(session, employee.attendance_code)
    print(f"[Attendance] Clock Out: {res_out['message']}")
    
    # Manually update clock_out to 5 PM
    rec.clock_out = datetime.combine(date.today(), time(17, 0)) # 5:00 PM
    AttendanceService.calculate_daily_stats(session, rec) # Recalculate
    session.commit()
    
    # Verify Stats
    print(f"[Verify] Duty Time: {rec.duty_time_hours}h (Expected ~7.9h)")
    print(f"[Verify] Late Hours: {rec.late_hours}h")
    
    # 6. Test Late Logic
    # Fake another day
    # We can't easily fake another day with current simple service without mocking date.today()
    
    # 7. Run Payroll
    print("--- Running Payroll ---")
    payroll = PayrollService.calculate_salary(session, employee.id, date.today().month, date.today().year)
    if payroll:
        print(f"[Payroll] Net Salary: {payroll['net_salary']}")
        print(f"[Payroll] Present Days: {payroll['present_days']}")
    else:
        print("[Payroll] Failed to calculate")

    print("--- Test Complete ---")

if __name__ == "__main__":
    run_test()
