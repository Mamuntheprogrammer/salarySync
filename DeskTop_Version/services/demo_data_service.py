from datetime import date, datetime, timedelta, time
from database import get_db_session
from models import (Company, BusinessArea, Shift, Designation, DesignationSubcategory, 
                   Employee, Attendance, HolidayCalendar, LeaveQuota, AdminUser)
import random

class DemoDataService:
    @staticmethod
    def populate_demo_data(session=None):
        """Populates the database with comprehensive demo data."""
        if not session:
            session = get_db_session()
            
        try:
            # 1. Company & Areas
            # Use same codes as the import template sample data so demo data
            # is consistent with what users see if they download/import a template.
            comp = session.query(Company).filter_by(code="HQ01").first()
            if not comp:
                comp = Company(code="HQ01", name="Global Tech Solutions")
                session.add(comp)
                session.flush()

            area_defs = [
                ("HR",  "Human Resources"),
                ("IT",  "Information Technology"),
                ("MKT", "Marketing"),
                ("SAL", "Sales"),
                ("SUP", "Support"),
                ("FIN", "Finance"),
            ]
            db_areas_map = {}
            for area_code, area_name in area_defs:
                ba = session.query(BusinessArea).filter_by(code=area_code, company_id=comp.id).first()
                if not ba:
                    ba = BusinessArea(code=area_code, name=area_name, company_id=comp.id)
                    session.add(ba)
                db_areas_map[area_code] = ba
            session.flush()
            
            # 2. Shifts – matching import template
            shifts = [
                {"name": "General", "start": time(9,0),  "end": time(18,0), "late": 15},
                {"name": "Morning", "start": time(6,0),  "end": time(14,0), "late": 10},
                {"name": "Evening", "start": time(14,0), "end": time(22,0), "late": 10},
                {"name": "Night",   "start": time(22,0), "end": time(6,0),  "late": 15},
                {"name": "Split 1", "start": time(8,0),  "end": time(17,0), "late": 15},
            ]
            db_shifts_map = {}
            for s in shifts:
                shift = session.query(Shift).filter_by(name=s["name"]).first()
                if not shift:
                    shift = Shift(name=s["name"], start_time=s["start"], end_time=s["end"],
                                  late_allowance_minutes=s["late"])
                    session.add(shift)
                db_shifts_map[s["name"]] = shift
            session.flush()
            
            # 3. Designations
            desigs = {
                "Manager": ["Senior", "Junior"],
                "Developer": ["Frontend", "Backend", "Fullstack"],
                "Sales Exec": ["Field", "In-house"]
            }
            for d_name, subs in desigs.items():
                deg = session.query(Designation).filter_by(name=d_name).first()
                if not deg:
                    deg = Designation(name=d_name)
                    session.add(deg)
                    session.flush()
                    
                for sub_name in subs:
                    sub = session.query(DesignationSubcategory).filter_by(name=sub_name, designation_id=deg.id).first()
                    if not sub:
                        sub = DesignationSubcategory(name=sub_name, designation_id=deg.id)
                        session.add(sub)
            session.flush()
            
            # 4. Employees – mirroring the import template's sample rows exactly
            # (employee codes 1001-1010, same company/area/shift references)
            emp_defs = [
                # (full_name,         area_code, shift_name, desig_name,  sub_name,    salary, active)
                ("John Doe",         "HR",  "General", "Manager",    "Senior",   50000, True),
                ("Jane Smith",        "IT",  "Morning", "Developer",  "Backend",  45000, True),
                ("Alice Johnson",     "IT",  "Morning", "Developer",  "Frontend", 42000, True),
                ("Bob Brown",         "MKT", "Evening", "Manager",    "Junior",   35000, True),
                ("Charlie Davis",     "SAL", "Evening", "Sales Exec", "Field",    30000, True),
                ("Eva Wilson",        "SUP", "Night",   "Manager",    "Senior",   40000, True),
                ("Frank Miller",      "HR",  "General", "Developer",  "Fullstack",15000, True),
                ("Grace Lee",         "HR",  "Night",   "Manager",    "Senior",   90000, True),
                ("Henry Taylor",      "FIN", "General", "Developer",  "Backend",  38000, False),
                ("Ivy Clark",         "IT",  "Split 1", "Developer",  "Frontend", 41000, True),
            ]

            employees = []
            for fname, area_code, shift_name, dname, subname, salary, active in emp_defs:
                emp = session.query(Employee).filter_by(full_name=fname).first()
                if not emp:
                    # Resolve designation and subcategory
                    deg = session.query(Designation).filter_by(name=dname).first()
                    sub = None
                    if deg and subname:
                        sub = session.query(DesignationSubcategory).filter_by(
                            name=subname, designation_id=deg.id).first()

                    area = db_areas_map.get(area_code)
                    shift = db_shifts_map.get(shift_name)

                    emp = Employee(
                        full_name=fname,
                        company_id=comp.id,
                        business_area_id=area.id if area else None,
                        shift_id=shift.id if shift else None,
                        designation_id=deg.id if deg else None,
                        designation_subcategory_id=sub.id if sub else None,
                        salary_base=salary,
                        is_active=active
                    )
                    session.add(emp)
                employees.append(emp)
            session.flush()
            
            # 5. Attendance History (Past 7 days)
            today = date.today()
            for day_offset in range(7):
                curr_date = today - timedelta(days=day_offset)
                
                # Check if data exists for this date to avoid duplication
                # (Simple check: if any attendance exists for this date, skip or be careful)
                # We'll just check per employee
                
                for emp in employees:
                    if session.query(Attendance).filter_by(employee_id=emp.id, date=curr_date).first():
                        continue
                        
                    # Randomize attendance
                    # 80% chance present
                    if random.random() < 0.8:
                        # Shift timings
                        shift = emp.shift
                        if not shift: continue
                        
                        # Randomize in/out
                        # In: Shift start +/- 20 mins
                        s_dt = datetime.combine(curr_date, shift.start_time)
                        in_variance = random.randint(-15, 45) # Mostly late for testing :P
                        clock_in = s_dt + timedelta(minutes=in_variance)
                        
                        # Out: Shift end +/- 60 mins
                        e_dt = datetime.combine(curr_date, shift.end_time)
                        out_variance = random.randint(-10, 120) # Frequently OT
                        clock_out = e_dt + timedelta(minutes=out_variance)
                        
                        # Calculate logic (re-use service logic or simplified?)
                        # We want the DB to look "calculated", so let's pre-calc simply
                        
                        duty_seconds = (clock_out - clock_in).total_seconds()
                        duty_h = round(duty_seconds / 3600, 2)
                        
                        late_h = 0.0
                        if in_variance > shift.late_allowance_minutes:
                            late_h = round((clock_in - s_dt).total_seconds() / 3600, 2)
                            
                        ot_h = 0.0
                        if out_variance > 0:
                            ot_h = round(out_variance / 60, 2)
                            
                        att = Attendance(
                            employee_id=emp.id,
                            date=curr_date,
                            clock_in=clock_in,
                            clock_out=clock_out,
                            duty_time_hours=duty_h,
                            late_hours=late_h,
                            overtime_hours=ot_h,
                            short_leave_hours=0.0
                        )
                        session.add(att)
            
            # 6. Holidays
            h_date = today + timedelta(days=10) # Future holiday
            if not session.query(HolidayCalendar).filter_by(date=h_date).first():
                hol = HolidayCalendar(name="Demo Festival", date=h_date, type="Festival", is_ot_eligible=True)
                session.add(hol)
                
            session.commit()
            return True, f"Demo data populated successfully. Added {len(employees)} Employees and Attendance history."
            
        except Exception as e:
            session.rollback()
            return False, f"Error generating data: {str(e)}"
