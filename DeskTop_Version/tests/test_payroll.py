from database import get_db_session
from services.payroll_service import PayrollService
from models import Employee
from datetime import date

def test_payroll():
    session = get_db_session()
    # Employee 500001
    emp = session.query(Employee).filter_by(emp_code='500001').first()
    if not emp:
        print("Employee 500001 not found")
        return

    today = date.today()
    month = today.month
    year = today.year
    
    print(f"Calculating Payroll for {emp.full_name} ({emp.emp_code}) - {month}/{year}")
    
    try:
        result = PayrollService.calculate_salary(session, emp.id, month, year)
        if result:
            print("Payroll Calculated Successfully!")
            print("-" * 30)
            for k, v in result.items():
                print(f"{k}: {v}")
            print("-" * 30)
        else:
            print("No result returned (inactive employee?)")
            
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payroll()
