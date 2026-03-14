import sys
import os
from datetime import datetime, time, date, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db
from models import Employee, Shift, Attendance, Company, BusinessArea
from services.attendance_service import AttendanceService
from services.shift_service import ShiftService

def test_late_calc():
    db.initialize()
    session = db.get_session()
    
    try:
        # 1. Setup Data
        print("Setting up test data...")
        
        # Company
        comp = session.query(Company).filter_by(code="TEST_C").first()
        if not comp:
            comp = Company(code="TEST_C", name="Test Company")
            session.add(comp)
            
        # Area
        ba = session.query(BusinessArea).filter_by(code="TA").first()
        if not ba:
            ba = BusinessArea(code="TA", name="Test Area", company=comp)
            session.add(ba)
            
        # Shift (9-18, 15m allowance)
        shift = session.query(Shift).filter_by(name="LateTestShift").first()
        if not shift:
            shift = ShiftService.create_shift(session, "LateTestShift", time(9,0), time(18,0), 15)
        
        # Employee
        emp = session.query(Employee).filter_by(emp_code="9999").first()
        if not emp:
            emp = Employee(
                emp_code="9999", 
                full_name="Late Tester", 
                company=comp, 
                business_area=ba,
                shift=shift
            )
            session.add(emp)
        else:
            emp.shift = shift # Ensure shift is set
            
        session.commit()
        
        # 2. Simulate Start of Day (Clean Attendance)
        today = date.today()
        session.query(Attendance).filter_by(employee_id=emp.id, date=today).delete()
        session.commit()
        
        # 3. Clock In LATE (at 9:30, allowance 15m -> Late by 30m = 0.5h)
        print("Clocking In at 9:30 (Late)...")
        # We resort to manual creation or mocking datetime.now() 
        # But AttendanceService.clock_in uses datetime.now().
        # So we can't easily use the Service for "Time Travel" unless we mock it.
        # Alternatively, we manually create the record and call calculate_daily_stats.
        # OR we modify the Service to accept a time argument (good for testing too).
        # For this repro, I will Insert record directly then call calculate logic if valid.
        
        # But wait, the USER issue is about the System Behavior.
        # If I manually Calculate, I am testing the Math, not the Workflow.
        # The Workflow is: User clicks Clock In -> Service.clock_in() -> (Missing Calc) -> DB.
        
        # Start with simple check: Does clock_in() call calc?
        # Reading the code (Step 418), I saw it DOES NOT.
        # So I don't need to run a script to prove it doesn't call it. The code is clear.
        # But I should verify that IF I call calc, it works.
        
        # Let's creating a record with 9:30 ClockIn and NO ClockOut.
        att = Attendance(
            employee_id=emp.id,
            date=today,
            clock_in=datetime.combine(today, time(9, 30)),
            clock_out=None
        )
        session.add(att)
        session.commit()
        
        print("Calling Calculate Daily Stats...")
        AttendanceService.calculate_daily_stats(session, att)
        session.commit()
        
        session.refresh(att)
        print(f"Late Hours: {att.late_hours}")
        
        if att.late_hours == 0.5:
             print("SUCCESS: Calculation works correctly if called.")
        elif att.late_hours == 0.0:
             print("FAILURE: Calculation did NOT update late_hours (likely due to missing clock_out check).")
        else:
             print(f"unexpected value: {att.late_hours}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_late_calc()
