import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import Company, BusinessArea, Employee, Designation, DesignationSubcategory
from services.employee_service import EmployeeService
from config import Config
from pathlib import Path

def run_test():
    print("--- Starting Designation Verification ---")
    
    # Force DB Reset for Test
    db_path = Path(Config.load_config().get('db_path'))
    if db_path.exists():
        try:
            os.remove(db_path)
            print("[OK] Deleted existing test database.")
        except:
            pass
            
    db.initialize()
    session = get_db_session()
    
    # Clean up
    session.query(Employee).delete()
    session.query(DesignationSubcategory).delete()
    session.query(Designation).delete()
    session.query(BusinessArea).delete()
    session.query(Company).delete()
    session.commit()
    
    # 1. Create Company & BA
    company = Company(code="999", name="Test Corp")
    session.add(company)
    session.commit()
    
    ba = BusinessArea(code="01", name="HQ", company_id=company.id)
    session.add(ba)
    session.commit()
    
    # 2. Create Designation & Subcategory
    des = Designation(name="Software Engineer")
    session.add(des)
    session.commit()
    print(f"[OK] Created Designation: {des.name}")
    
    sub = DesignationSubcategory(name="Senior", designation_id=des.id)
    session.add(sub)
    session.commit()
    print(f"[OK] Created Subcategory: {sub.name}")
    
    # 3. Create Employee with Designation
    data = {
        "full_name": "Alice Dev",
        "company_id": company.id,
        "business_area_id": ba.id,
        "salary_base": 100000,
        "designation_id": des.id,
        "designation_subcategory_id": sub.id
    }
    
    emp = EmployeeService.create_employee(session, data)
    print(f"[OK] Created Employee: {emp.full_name} (Code: {emp.attendance_code})")
    
    # 4. Verify Relationship
    e = session.query(Employee).filter_by(id=emp.id).first()
    
    print(f"Designation: {e.designation.name if e.designation else 'None'}")
    print(f"Subcategory: {e.designation_subcategory.name if e.designation_subcategory else 'None'}")
    
    if e.designation and e.designation.name == "Software Engineer" and \
       e.designation_subcategory and e.designation_subcategory.name == "Senior":
        print("[SUCCESS] Employee correctly assigned to designation.")
    else:
        print("[FAILURE] Designation assignment incorrect.")

if __name__ == "__main__":
    run_test()
