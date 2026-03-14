from database import get_db_session
from models import Employee, Company

session = get_db_session()
emps = session.query(Employee).all()

print(f"Total Employees: {len(emps)}")
for e in emps:
    c_code = e.company.code if e.company else "None"
    print(f"Emp: {e.full_name} ({e.emp_code}) | Company: {c_code}")
