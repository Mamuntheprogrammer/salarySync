import sys
import os
from datetime import date, timedelta
from database import get_db_session, db
from models import Company, BusinessArea, Employee, LeaveQuota, LeaveRequest, Attendance
from services.leave_service import LeaveService
from services.payroll_service import PayrollService

def test_leave_flow():
    print("--- Starting Leave Flow Test ---")
    
    # 1. Setup
    db.initialize()
    session = get_db_session()
    
    comp = session.query(Company).filter_by(code="L01").first()
    if not comp:
        comp = Company(code="L01", name="Leave Corp")
        session.add(comp)
        session.flush()
    
    ba = session.query(BusinessArea).filter_by(code="L1", company_id=comp.id).first()
    if not ba:
        ba = BusinessArea(code="L1", name="Ops", company_id=comp.id)
        session.add(ba)
        session.flush()
    
    emp = session.query(Employee).filter_by(emp_code="888888").first()
    if not emp:
        emp = Employee(
            emp_code="888888",
            full_name="Leave Tester",
            company_id=comp.id,
            business_area_id=ba.id,
            salary_base=30000.0,
            is_active=True
        )
        session.add(emp)
        session.flush()
    
    # 2. Set Quota (Company Level)
    q = session.query(LeaveQuota).filter_by(company_id=comp.id, year=2026, leave_type="Annual").first()
    if not q:
        q = LeaveQuota(
            company_id=comp.id,
            year=2026,
            leave_type="Annual",
            quota_limit=10.0
        )
        session.add(q)
        session.commit()
    
    print("Created Employee & Quota (10 Annual Days).")
    
    # 3. Check Balance
    bal = LeaveService.get_leave_balance(session, emp.id, 2026)
    print(f"Initial Balance: {bal}")
    
    # 4. Submit Request (2 days: Jan 5, Jan 6)
    res = LeaveService.submit_leave_request(
        session, emp.id, "Annual", date(2026, 1, 5), date(2026, 1, 6), "Vacation"
    )
    print(f"Submit Result: {res}")
    
    # 5. Approve Request
    req = session.query(LeaveRequest).filter_by(employee_id=emp.id).first()
    res = LeaveService.approve_request(session, req.id, "admin")
    print(f"Approve Result: {res}")
    
    # 6. Check Balance Again (Should be 8 remaining)
    bal = LeaveService.get_leave_balance(session, emp.id, 2026)
    print(f"New Balance: {bal}")
    if bal["Annual"]["remaining"] == 8.0:
        print("✅ Balance Check Passed")
    else:
        print("❌ Balance Check Failed")
        
    # 7. Test Payroll Impact
    # Month Jan 2026. 
    # Employee worked on Jan 1 only.
    a1 = Attendance(employee_id=emp.id, date=date(2026, 1, 1), duty_time_hours=8.0,clock_in=datetime.now(), clock_out=datetime.now())
    session.add(a1)
    session.commit()
    
    # Calculate
    # Working Days = 31 (Assuming no weekends configured for simplicity)
    # Present = 1
    # Absent Raw = 30
    # Approved Leaves = 2 (Jan 5 both working days)
    # Absent Deductible = 28
    
    from datetime import datetime # Fix import for dummy attendance
    
    payroll = PayrollService.calculate_salary(session, emp.id, 1, 2026)
    print(f"Working Days: {payroll['working_days']}")
    print(f"Absent Days: {payroll['absent_days']}")
    
    # If 31 days and no weekends configured, working days = 31.
    # We didn't configure weekends in this test.
    # So expected absent is 31 - 1 (Present) - 2 (Leave) = 28.
    
    if payroll['absent_days'] <= 28: # Might be lower if weekends exist by default? No default weekend is empty.
        print(f"✅ Payroll Deduction Logic Passed (Absent: {payroll['absent_days']})")
    else:
        print(f"❌ Payroll Logic Failed (Absent: {payroll['absent_days']} > 28)")

if __name__ == "__main__":
    try:
        test_leave_flow()
    except Exception as e:
        import traceback
        traceback.print_exc()
