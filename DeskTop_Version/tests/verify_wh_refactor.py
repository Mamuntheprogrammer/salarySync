import sys
import os
import openpyxl

sys.path.append(os.getcwd())
from models import WeeklyHoliday, Shift
from database import get_db_session
from services.legacy_import_service import LegacyImportService

# Setup dummy data
def verify_refactor():
    print("Verifying Weekly Holiday Refactor...")
    session = get_db_session()
    
    # 1. Ensure a Shift exists
    shift_name = "Test Night Shift"
    s = session.query(Shift).filter_by(name=shift_name).first()
    if not s:
        import datetime
        s = Shift(name=shift_name, start_time=datetime.time(22,0), end_time=datetime.time(6,0))
        session.add(s)
        session.commit()
    print(f"Shift '{shift_name}' ID: {s.id}")
    
    # 2. Generate Template
    path = LegacyImportService.generate_template(["weekly_holidays"], "verify_wh.xlsx")
    print(f"Template generated at {path}")
    
    # 3. Create Import File with Data
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "weekly_holidays"
    # Header: ["day_of_week", "company_code", "business_area_code", "shift_name"]
    ws.append(["day_of_week", "company_code", "business_area_code", "shift_name"])
    # Data: Friday off for Test Night Shift
    ws.append(["Friday", "", "", shift_name])
    
    test_file = "test_wh_import.xlsx"
    wb.save(test_file)
    print("Created test import file.")
    
    # 4. Run Import
    print("Running import...")
    count, errors = LegacyImportService.import_table_data(test_file, "weekly_holidays")
    print(f"Imported: {count}, Errors: {errors}")
    
    if errors:
        print("Test FAILED with import errors.")
        return

    # 5. Verify Database
    wh = session.query(WeeklyHoliday).filter_by(shift_id=s.id, day_of_week=4).first()
    if wh:
        print("SUCCESS: Weekly Holiday found for Shift.")
    else:
        print("FAILURE: Weekly Holiday NOT found in DB.")
        
    # Clean up
    if wh: session.delete(wh)
    session.commit()

if __name__ == "__main__":
    verify_refactor()
