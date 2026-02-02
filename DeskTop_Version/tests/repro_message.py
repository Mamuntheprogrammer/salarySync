import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from services.employee_service import EmployeeService
from services.attendance_service import AttendanceService
from models import Company, BusinessArea, Shift, Employee, Attendance, ShortLeave
from datetime import datetime, time, date

def run_test():
    print("--- Starting Message Format Verification ---")
    
    # 1. Initialize DB
    db.initialize()
    session = get_db_session()
    
    # Clean up
    session.query(ShortLeave).delete()
    session.query(Attendance).delete()
    session.query(Employee).delete()
    session.query(BusinessArea).delete()
    session.query(Company).delete()
    session.commit()
    
    # 2. Setup Data
    company = Company(code="TEST", name="Test Corp")
    session.add(company)
    session.commit()
    
    ba = BusinessArea(code="HQ", name="HQ", company_id=company.id)
    session.add(ba)
    session.commit()
    
    emp_data = {
        "full_name": "John Doe",
        "company_id": company.id,
        "business_area_id": ba.id,
        "salary_base": 50000
    }
    employee = EmployeeService.create_employee(session, emp_data)
    print(f"Created Employee: {employee.full_name} (Code: {employee.attendance_code})")
    
    # 3. Test Clock In
    print("\n[Testing Clock In]")
    res_in = AttendanceService.clock_in(session, employee.attendance_code)
    print(f"Message: {res_in['message']}")
    
    # 4. Test Short Leave
    print("\n[Testing Short Leave]")
    res_leave = AttendanceService.record_short_leave(
        session, 
        employee.attendance_code, 
        "Personal", 
        time(10, 0), 
        time(10, 30)
    )
    print(f"Message: {res_leave['message']}")
    
    # 5. Test Clock Out
    print("\n[Testing Clock Out]")
    res_out = AttendanceService.clock_out(session, employee.attendance_code)
    print(f"Message: {res_out['message']}")
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
