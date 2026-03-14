import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import AdminUser, Employee, Company, BusinessArea
from services.user_service import UserService
from config import Config
from pathlib import Path

def run_test():
    print("--- Starting RBAC Verification ---")
    
    # 1. Reset DB
    db_path = Path(Config.load_config().get('db_path'))
    if db_path.exists():
        try:
            os.remove(db_path)
        except: pass
        
    db.initialize()
    session = get_db_session()
    
    # 2. Create Company/Employee
    company = Company(code="TST", name="Test Corp")
    session.add(company)
    ba = BusinessArea(code="HQ", name="HQ", company=company)
    session.add(ba)
    session.commit()
    
    emp = Employee(emp_code="123456", full_name="John User", company_id=company.id, business_area_id=ba.id)
    session.add(emp)
    session.commit()
    
    # 3. Create Users
    print("Creating Admin...")
    admin = UserService.create_user(session, "admin", "admin123", "admin")
    
    print(f"Creating User linked to {emp.full_name}...")
    user = UserService.create_user(session, "john", "pass123", "user", employee_id=emp.id)
    
    # 4. Authenticate
    print("\n[Testing Authentication]")
    auth_admin = UserService.authenticate(session, "admin", "admin123")
    if auth_admin and auth_admin.role == "admin":
        print("[SUCCESS] Admin Login OK")
    else:
        print("[FAILURE] Admin Login Failed")
        
    auth_user = UserService.authenticate(session, "john", "pass123")
    if auth_user and auth_user.role == "user" and auth_user.employee.full_name == "John User":
        print("[SUCCESS] User Login OK with Employee Link")
    else:
        print("[FAILURE] User Login Failed")
        
    auth_fail = UserService.authenticate(session, "admin", "wrong")
    if not auth_fail:
        print("[SUCCESS] Bad Password Blocked")
    else:
        print("[FAILURE] Bad Password Allowed")
        
    print("\n--- RBAC Verification Complete ---")

if __name__ == "__main__":
    run_test()
