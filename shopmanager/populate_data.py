import os
import sys
import django
import pandas as pd
from datetime import datetime, time, timedelta, date

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopmanager.settings')
django.setup()

from company.models import CompanyCode, BusinessArea
from employee.models import Employee, Department, Designation, JobHistory
from leave.models import Shift, LeaveType, HolidayCalendar, EmployeeLeaveQuota, LeaveRequest
from attendance.models import Attendance, BreakRecord
from payroll.models import SalaryRecord
from django.utils import timezone

def parse_time(val):
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, datetime):
        return val.time()
    try:
        return datetime.strptime(str(val).split('.')[0], "%H:%M:%S").time()
    except (ValueError, TypeError):
        return None

def run():
    print("Starting comprehensive data population...")
    
    # 1. Company & Core
    company, _ = CompanyCode.objects.get_or_create(
        companycode="C001", defaults={"name": "Tech Corp", "description": "Main Company"}
    )
    business_area, _ = BusinessArea.objects.get_or_create(
        code="BA001", defaults={"name": "Dhaka HQ", "company": company}
    )
    
    # 2. Leave Settings
    casual_leave, _ = LeaveType.objects.get_or_create(
        name="Casual Leave", defaults={"yearly_quota": 10, "description": "Personal matters"}
    )
    sick_leave, _ = LeaveType.objects.get_or_create(
        name="Sick Leave", defaults={"yearly_quota": 14, "description": "Medical reasons"}
    )
    
    HolidayCalendar.objects.get_or_create(
        name="Victory Day",
        date=date(2025, 12, 16),
        defaults={"is_public_holiday": True, "business_area": business_area}
    )

    shift, _ = Shift.objects.get_or_create(
        shift_code="GS",
        defaults={
            "name": "General Shift", "business_area": business_area,
            "start_time": time(9, 0), "end_time": time(18, 0),
            "daily_hours": 9.00
        }
    )
    
    dept, _ = Department.objects.get_or_create(name="General", defaults={"business_area": business_area})
    desig, _ = Designation.objects.get_or_create(title="Staff")

    # 3. Read Excel
    file_path = 'sample_data.xlsx'
    if not os.path.exists(file_path):
        print("Excel file not found.")
        return

    xl = pd.ExcelFile(file_path)
    
    for sheet_name in xl.sheet_names:
        print(f"Processing: {sheet_name}")
        emp_code = f"EMP-{sheet_name.replace(' ', '')[:5].upper()}"
        
        # Employee
        employee, created = Employee.objects.get_or_create(
            emp_code=emp_code,
            defaults={
                "full_name": sheet_name,
                "business_area": business_area, "department": dept,
                "designation": desig, "shift": shift,
                "join_date": date(2024, 1, 1), "base_salary": 20000.00
            }
        )
        
        # Quotas
        for lt in [casual_leave, sick_leave]:
            EmployeeLeaveQuota.objects.get_or_create(
                employee=employee, leave_type=lt, year=2025,
                defaults={"allocated": lt.yearly_quota, "used": 0}
            )

        # Job History (Sample)
        # Ensure at least one history record exists
        if not JobHistory.objects.filter(employee=employee).exists():
            JobHistory.objects.create(
                employee=employee, department=dept, designation=desig,
                base_salary=18000.00, start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31), reason="Initial Joining"
            )

        # Attendance from Excel
        # Based on inspection:
        # Row 1 (header=0): Unnamed...
        # Row 2 (idx 0): Mehedi...
        # Row 5 (idx 3): DATE... -> Excel Row 5 is the header for data table
        # So we use header=4 (0-indexed)
        try:
            df = xl.parse(sheet_name, header=4)
        except IndexError:
             # Fallback if sheet structure varies
             df = xl.parse(sheet_name, header=3)
             
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Debugging print
        # print(f"Columns: {df.columns.tolist()}")
        
        monthly_work_hours = timedelta()
        
        for index, row in df.iterrows():
            date_val = row.get('DATE')
            
            # Pandas Timestamp is compatible with datetime but verification might be tricky
            # Let's be lenient
            if pd.isna(date_val):
                continue
                
            try:
                attendance_date = pd.to_datetime(date_val).date()
            except Exception:
                continue

            check_in_raw = row.get('TIME IN')
            check_out_raw = row.get('TIME OUT')
            
            check_in = parse_time(check_in_raw)
            check_out = parse_time(check_out_raw)
            
            if check_in:
                att, created_att = Attendance.objects.update_or_create(
                    employee=employee, date=attendance_date,
                    defaults={"check_in": check_in, "check_out": check_out}
                )
                
                # Sample Break
                if created_att:
                    BreakRecord.objects.get_or_create(
                         attendance=att,
                         defaults={
                            "break_start": time(13,0), "break_end": time(14,0),
                            "duration": timedelta(hours=1)
                         }
                    )
                
                # Accumulate hours for dummy Salary Record
                monthly_work_hours += timedelta(hours=8) # Dummy calculation

        # Leave Request (Sample)
        LeaveRequest.objects.get_or_create(
            employee=employee, start_date=date(2025, 9, 5), end_date=date(2025, 9, 6),
            defaults={
                "leave_type": casual_leave, "reason": "Family function",
                "status": "APPROVED"
            }
        )
        
        # Salary Record (Sample for September)
        SalaryRecord.objects.update_or_create(
            employee=employee, month=date(2025, 9, 1),
            defaults={
                "total_work_hours": monthly_work_hours,
                "overtime_hours": timedelta(0),
                "basic_salary": 20000.00,
                "overtime_pay": 0.00,
                "deductions": 0.00,
                "net_salary": 20000.00
            }
        )

    print("Comprehensive data population finished.")

if __name__ == "__main__":
    run()
