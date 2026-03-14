import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session, Base, db
from models import Company, BusinessArea, Employee, HolidayCalendar, Shift
from services.calendar_service import CalendarService
from datetime import date, time

def test_holiday_codes():
    print("Setting up test database...")
    # Ensure initialized
    get_db_session()
    engine = db.engine
    
    # Drop table to ensure schema update
    try:
        HolidayCalendar.__table__.drop(engine)
    except Exception as e:
        print(f"Table drop skipped: {e}")

    Base.metadata.create_all(engine)
    session = get_db_session()
    
    try:
        # Cleanup
        session.query(HolidayCalendar).delete()
        session.query(Employee).delete()
        session.query(BusinessArea).delete()
        session.query(Company).delete()
        session.query(Shift).delete()
        session.flush()

        # Setup
        c1 = Company(code="C1", name="Test Comp 1")
        session.add(c1)
        session.flush()

        ba1 = BusinessArea(code="BA1", name="Test BA 1", company_id=c1.id)
        session.add(ba1)
        session.flush()

        shift = Shift(name="Gen", start_time=time(9,0), end_time=time(18,0)) # Correct types
        session.add(shift)
        session.flush() # Fail if strict type checking on Time? models say Time. 
        # But wait, Shift start_time is Time. date() object is not Time. 
        # Actually I don't need shift for this test but Employee needs FK? nullable=True (actually nullable=True in my memory of models.py? Let's check. 
        # Employee: shift_id nullable=True. Good.

        e1 = Employee(
            emp_code="E001", 
            full_name="Emp 1", 
            company_id=c1.id, 
            business_area_id=ba1.id,
            is_active=True
        )
        session.add(e1)
        session.flush()

        # Create Holidays
        # 1. Global
        h_global = HolidayCalendar(description="Global Hol", date=date(2025, 1, 1), type="National", year=2025)
        # 2. Company Specific (C1)
        h_c1 = HolidayCalendar(description="C1 Hol", date=date(2025, 2, 1), type="Company", year=2025, company_code="C1")
        # 3. BA Specific (BA1)
        h_ba1 = HolidayCalendar(description="BA1 Hol", date=date(2025, 3, 1), type="Local", year=2025, business_area_code="BA1")
        # 4. Unrelated (C2)
        h_c2 = HolidayCalendar(description="C2 Hol", date=date(2025, 4, 1), type="Company", year=2025, company_code="C2")
        
        session.add_all([h_global, h_c1, h_ba1, h_c2])
        session.commit()

        print("Verifying Holidays for Employee E1 (C1, BA1)...")
        
        # Test 1: Global
        res = CalendarService.is_holiday(session, date(2025, 1, 1), e1)
        assert res["is_holiday"] == True, "Failed Global Holiday"
        print("PASS: Global Holiday")

        # Test 2: C1
        res = CalendarService.is_holiday(session, date(2025, 2, 1), e1)
        assert res["is_holiday"] == True, "Failed Company Holiday"
        print("PASS: Company Holiday")

        # Test 3: BA1
        res = CalendarService.is_holiday(session, date(2025, 3, 1), e1)
        assert res["is_holiday"] == True, "Failed FA Holiday"
        print("PASS: BA Holiday")

        # Test 4: C2 (Should be False)
        res = CalendarService.is_holiday(session, date(2025, 4, 1), e1)
        assert res["is_holiday"] == False, "Failed Isolation (Caught C2 Holiday)"
        print("PASS: Isolation Check")
        
        print("\nALL TESTS PASSED")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_holiday_codes()
