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
            comp = session.query(Company).filter_by(code="DEMO").first()
            if not comp:
                comp = Company(code="DEMO", name="Demo Corp Ltd.")
                session.add(comp)
                session.flush()
                
            areas = ["HR", "IT", "Sales", "Operations"]
            db_areas = []
            for i, area_name in enumerate(areas):
                ba = session.query(BusinessArea).filter_by(code=f"D0{i+1}", company_id=comp.id).first()
                if not ba:
                    ba = BusinessArea(code=f"D0{i+1}", name=area_name, company_id=comp.id)
                    session.add(ba)
                db_areas.append(ba)
            session.flush()
            
            # 2. Shifts
            shifts = [
                {"name": "General", "start": time(9,0), "end": time(18,0)},
                {"name": "Morning", "start": time(6,0), "end": time(14,0)},
                {"name": "Evening", "start": time(14,0), "end": time(22,0)},
            ]
            db_shifts = []
            for s in shifts:
                shift = session.query(Shift).filter_by(name=s["name"]).first()
                if not shift:
                    shift = Shift(name=s["name"], start_time=s["start"], end_time=s["end"], late_allowance_minutes=15)
                    session.add(shift)
                db_shifts.append(shift)
            session.flush()
            
            # 3. Designations
            desigs = {
                "Manager": ["Senior", "Junior"],
                "Developer": ["Frontend", "Backend", "Fullstack"],
                "Sales Exec": ["Field", "In-house"]
            }
            db_desigs = [] # List of (deg, sub) tuples
            
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
                    db_desigs.append((deg, sub))
            session.flush()
            
            # 4. Employees
            # Create 10 demo employees
            names = ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis", 
                     "Eva Wilson", "Frank Miller", "Grace Lee", "Henry Taylor", "Ivy Clark"]
            
            employees = []
            for i, name in enumerate(names):
                acode = f"100{i}"
                emp = session.query(Employee).filter_by(attendance_code=acode).first()
                if not emp:
                    # Random assignment
                    deg, sub = random.choice(db_desigs)
                    
                    # session.add(ba) acts weird if ba isn't flushed or re-queried properly in loop? 
                    # Assuming db_areas are attached or usable.
                    # safer to re-query if detached, but flush should keep them attached in same session.
                    
                    emp = Employee(
                        attendance_code=acode,
                        full_name=name,
                        company_id=comp.id,
                        business_area_id=random.choice(db_areas).id if db_areas else None,
                        shift_id=random.choice(db_shifts).id if db_shifts else None,
                        designation_id=deg.id,
                        designation_subcategory_id=sub.id,
                        salary_base=random.randint(3000, 8000) * 10,
                        is_active=True
                    )
                    session.add(emp)
                    employees.append(emp)
                else:
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
