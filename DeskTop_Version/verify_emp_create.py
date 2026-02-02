import sys
import os
import openpyxl

sys.path.append(os.getcwd())
from models import Employee
from database import get_db_session
from services.legacy_import_service import LegacyImportService

def verify_emp_create():
    print("Verifying Employee Creation via Import...")
    session = get_db_session()
    
    # 1. Ensure test employee does NOT exist
    test_code = "999999"
    emp = session.query(Employee).filter_by(attendance_code=test_code).first()
    if emp:
        session.delete(emp)
        session.commit()
        print(f"Deleted existing test employee {test_code}")
    
    # 2. Create Import File
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "employees"
    # Headers from schema
    ws.append(['attendance_code', 'full_name'])
    ws.append([test_code, "New Auto Created Employee"])
    
    test_file = "test_emp_create.xlsx"
    wb.save(test_file)
    
    # 3. Run Import
    print("Running import...")
    count, errors = LegacyImportService.import_table_data(test_file, "employees")
    print(f"Imported: {count}, Errors: {errors}")
    
    if errors:
        print("Import failed with errors.")
        return

    # 4. Verify DB
    emp = session.query(Employee).filter_by(attendance_code=test_code).first()
    if emp:
        print(f"SUCCESS: Employee {test_code} created. Name: {emp.full_name}")
        # Clean up
        session.delete(emp)
        session.commit()
    else:
        print("FAILURE: Employee NOT created.")

if __name__ == "__main__":
    verify_emp_create()
