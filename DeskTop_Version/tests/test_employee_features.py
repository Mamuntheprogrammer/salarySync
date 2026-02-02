import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import Employee, Company, BusinessArea, Shift
from services.employee_service import EmployeeService
from services.payroll_service import PayrollService
from services.attendance_service import AttendanceService
from config import Config
from pathlib import Path

def run_test():
    print("--- Starting Employee Features Verification ---")
    
    # 1. Reset DB
    db_path = Path(Config.load_config().get('db_path'))
    if db_path.exists():
        try: os.remove(db_path)
        except: pass
        
    db.initialize()
    session = get_db_session()
    
    # Create Company
    c = Company(code="TEST", name="Test Corp")
    session.add(c)
    session.commit()
    ba = BusinessArea(code="HQ", name="HQ", company_id=c.id)
    session.add(ba)
    session.commit()
    
    # 2. Create Active Employee
    print("Creating Active Employee...")
    e1 = EmployeeService.create_employee(session, {
        "full_name": "Active User", "company_id": c.id, "business_area_id": ba.id, "salary_base": 1000, "is_active": True
    })
    
    # 3. Create Inactive Employee
    print("Creating Inactive Employee...")
    e2 = EmployeeService.create_employee(session, {
        "full_name": "Inactive User", "company_id": c.id, "business_area_id": ba.id, "salary_base": 1000, "is_active": False
    })
    
    # 4. Verify Payroll Exclusion
    # Active should get payroll
    print("\n[Payroll Check]")
    p1 = PayrollService.calculate_salary(session, e1.id, 1, 2024)
    if p1: print("[SUCCESS] Active User gets payroll")
    else: print("[FAILURE] Active User NO payroll")
    
    p2 = PayrollService.calculate_salary(session, e2.id, 1, 2024)
    if not p2: print("[SUCCESS] Inactive User excluded from payroll")
    else: print("[FAILURE] Inactive User GOT payroll")
    
    # 5. Verify Attendance Blocking
    print("\n[Attendance Check]")
    # Active Clock In
    res1 = AttendanceService.clock_in(session, e1.attendance_code)
    if res1['success']: print("[SUCCESS] Active User can Clock In")
    else: print(f"[FAILURE] Active User blocked: {res1['message']}")
    
    # Inactive Clock In
    res2 = AttendanceService.clock_in(session, e2.attendance_code)
    if not res2['success'] and "inactive" in res2['message'].lower():
        print("[SUCCESS] Inactive User blocked from Clock In")
    else:
        print(f"[FAILURE] Inactive User NOT blocked: {res2}")
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
