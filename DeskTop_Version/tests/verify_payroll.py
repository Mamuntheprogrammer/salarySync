import sys
import os
from datetime import date
from database import get_db_session, db
from models import Company, BusinessArea, Employee, HolidayCalendar, WeeklyHoliday, Attendance, PayrollConfig
from services.payroll_service import PayrollService

def test_payroll_logic():
    print("--- Starting Payroll Logic Test (Company Hierarchy) ---")
    
    # 1. Setup DB
    db.initialize() # Check tables exist
    session = get_db_session()
    
    # Cleanup previous run data if any (though reset script ran)
    # session.query(Attendance).delete()
    # session.query(HolidayCalendar).delete()
    # session.query(WeeklyHoliday).delete()
    # session.query(Employee).delete()
    # session.query(BusinessArea).delete()
    # session.query(Company).delete()
    # session.commit()
    
    # Create Company & BA
    comp = Company(code="001", name="Test Corp")
    session.add(comp)
    session.flush()
    
    ba = BusinessArea(code="10", name="HQ", company_id=comp.id)
    session.add(ba)
    session.flush()
    
    # Create Employee
    emp = Employee(
        emp_code="100001",
        full_name="John Doe",
        company_id=comp.id,
        business_area_id=ba.id,
        salary_base=30000.0,
        is_active=True
    )
    session.add(emp)
    session.flush()
    
    print(f"Created Employee: {emp.full_name} (Comp: {comp.name}, BA: {ba.name})")
    
    # 2. Setup Calendar
    # Month: January 2026
    
    # Scenario:
    # 1. Company Level Weekend = Friday (4)
    # 2. Company Level Holiday = Jan 15th
    # 3. BA Level Override? No, let's stick to simple first.
    
    weekend_comp = WeeklyHoliday(day_of_week=4, company_id=comp.id) 
    session.add(weekend_comp)
    
    hol_comp = HolidayCalendar(
        date=date(2026, 1, 15), 
        year=2026, 
        description="Company Holiday", 
        type="Company",
        company_id=comp.id,
        is_ot_eligible=True # User Q: Work on holiday handled? Verified here.
    )
    session.add(hol_comp)
    session.commit()
    
    print("Configured Company Level: Friday as Weekend and Jan 15 as Holiday (OT Eligible).")
    
    # 3. Create Attendance
    # Working Days = 31 - 5 (Fri) - 1 (Jan 15) = 25
    
    # Employee Attendnace:
    # Worked on Jan 15 (Holiday) -> Should be Holiday OT.
    # Worked on Jan 1 (Thu) -> Regular Present.
    
    a1 = Attendance(
        employee_id=emp.id,
        date=date(2026, 1, 1),
        duty_time_hours=8.0,
        late_hours=0.0
    )
    session.add(a1)
    
    a2 = Attendance(
        employee_id=emp.id,
        date=date(2026, 1, 15),
        duty_time_hours=4.0,
        # is_holiday_ot flag is usually set by system on clock out or calc.
        # But we are manually inserting. 
        # AttendanceService would set it. 
        # Payroll Service DOES NOT check calendar again for OT Flag if manually inserted WITHOUT flag.
        # But Payroll Service recalculates stats? No, it trusts Attendance fields usually.
        # WAIT. My previous AttendanceService update SETS the flag.
        # But here I am inserting rows directly.
        # I should run 'calculate_daily_stats'? Or simulate what it does.
        # Let's NOT set flag manually and see if Payroll detects it?
        # NO, PayrollService uses CalendarService to detect holidays for absent calc, 
        # but treats 'overtime_hours' based on Attendance record.
        # So I must simulate what 'clock_out' does.
    )
    # Simulate Logic:
    a2.is_holiday_ot = True # Because Jan 15 is Comp Holiday OT Eligible
    a2.overtime_hours = 4.0
    session.add(a2)
    
    session.commit()
    
    # 4. Run Payroll
    print("Calculating Payroll for Jan 2026...")
    result = PayrollService.calculate_salary(session, emp.id, 1, 2026)
    
    print("\n--- Result ---")
    print(f"Working Days: {result['working_days']} (Expected: 25)")
    print(f"Present Days: {result['present_days']} (Expected: 2)") # 1 Reg + 1 Hol
    print(f"Absent Days: {result['absent_days']} (Expected: 24)")
    # Absent = Working (25) - PresentOnWorking(1) = 24. 
    # Jan 15 is Holiday, so presence there is ignored for WorkingDay count.
    
    print(f"Holiday OT Pay: {result['holiday_ot_pay']} (Expected: 4h * Rate * 2.0)")
    
    if result['working_days'] == 25 and result['absent_days'] == 24:
        print("\n✅ TEST PASSED: Company Level Logic works.")
    else:
        print("\n❌ TEST FAILED: mismatch.")

if __name__ == "__main__":
    try:
        test_payroll_logic()
    except Exception as e:
        import traceback
        traceback.print_exc()
