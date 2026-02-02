import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import Employee, Company, BusinessArea, Shift
from services.employee_service import EmployeeService
from config import Config
from pathlib import Path

def run_test():
    print("--- Starting Employee Update Verification ---")
    
    # 1. Reset DB
    db_path = Path(Config.load_config().get('db_path'))
    if db_path.exists():
        try: os.remove(db_path)
        except: pass
    db.initialize()
    session = get_db_session()
    
    # Create Company
    c = Company(code="TST", name="Test Corp")
    session.add(c)
    session.flush()
    ba = BusinessArea(code="HQ", name="HQ", company_id=c.id)
    session.add(ba)
    session.flush()
    
    c2 = Company(code="AC", name="Another Corp")
    session.add(c2)
    session.flush()
    ba2 = BusinessArea(code="BR", name="Branch", company_id=c2.id)
    session.add(ba2)
    session.commit()
    
    # 2. Create Employee
    print("Creating Employee...")
    e1 = EmployeeService.create_employee(session, {
        "full_name": "Test User", "company_id": c.id, "business_area_id": ba.id, "salary_base": 1000
    })
    
    print(f"Original: {e1.full_name}, Comp: {e1.company.code}, Sal: {e1.salary_base}")
    
    # 3. Update All Fields
    print("Updating Employee...")
    EmployeeService.update_employee(session, e1.id, {
        "full_name": "Updated User",
        "company_id": c2.id,
        "business_area_id": ba2.id,
        "salary_base": 2000
    })
    
    session.refresh(e1)
    
    print(f"Updated: {e1.full_name}, Comp: {e1.company.code}, Sal: {e1.salary_base}")
    
    if e1.full_name == "Updated User" and e1.company.code == "AC" and e1.salary_base == 2000:
        print("[SUCCESS] Employee Updated Correctly")
    else:
        print("[FAILURE] Employee Update Mismatch")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
