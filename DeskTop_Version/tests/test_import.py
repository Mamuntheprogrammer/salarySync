import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import Employee, Company
from services.import_service import ImportService
from config import Config
from pathlib import Path
import openpyxl

def run_test():
    print("--- Starting Excel Import Verification ---")
    
    # 1. Reset DB
    db_path = Path(Config.load_config().get('db_path'))
    if db_path.exists():
        try: os.remove(db_path)
        except: pass
    db.initialize()
    
    # 2. Generate Template
    tpl_path = "test_template.xlsx"
    if os.path.exists(tpl_path): os.remove(tpl_path)
    
    print("Generating Template...")
    ImportService.generate_template(tpl_path)
    
    if os.path.exists(tpl_path):
        print("[SUCCESS] Template generated")
    else:
        print("[FAILURE] Template not found")
        return
        
    # 3. Add Dummy Data to Template
    wb = openpyxl.load_workbook(tpl_path)
    
    # Add Company
    ws_co = wb["Companies"]
    ws_co.append(["IMP", "Imported Corp"])
    
    # Add Business Area
    ws_ba = wb["BusinessAreas"]
    ws_ba.append(["IMP", "HQ", "Headquarters"])
    
    # Add Employee
    ws_emp = wb["Employees"]
    # emp_code, full_name, company_code, area_code, shift_name, designation_name, subcategory_name, salary_base, is_active
    ws_emp.append(["999001", "Imported User", "IMP", "HQ", "", "", "", 5000, True])
    
    wb.save(tpl_path)
    print("Dummy data added to Excel.")
    
    # 4. Parse Sheets
    sheets = ImportService.get_sheet_names(tpl_path)
    print(f"Detected Sheets: {sheets}")
    if "Companies" in sheets and "Employees" in sheets:
        print("[SUCCESS] Sheets detected")
    else:
        print("[FAILURE] Sheets detection failed")
        
    # 5. Import Data
    print("Importing Data...")
    count, errors = ImportService.import_data(tpl_path, ["Companies", "BusinessAreas", "Employees"])
    
    print(f"Imported Count: {count}")
    if errors:
        print(f"Errors: {errors}")
        
    # 6. Verify processed data in DB
    session = get_db_session()
    c = session.query(Company).filter_by(code="IMP").first()
    e = session.query(Employee).filter_by(emp_code="999001").first()
    
    if c and c.name == "Imported Corp":
        print("[SUCCESS] Company imported")
    else:
        print("[FAILURE] Company import failed")
        
    if e and e.full_name == "Imported User":
        print("[SUCCESS] Employee imported")
    else:
        print("[FAILURE] Employee import failed")
        
    # Cleanup
    if os.path.exists(tpl_path):
        try: os.remove(tpl_path)
        except: pass

    print("--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
