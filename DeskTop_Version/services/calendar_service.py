from sqlalchemy.orm import Session
from models import HolidayCalendar, WeeklyHoliday, Employee
from datetime import date, timedelta
import calendar

class CalendarService:
    @staticmethod
    def is_holiday(session: Session, check_date: date, employee: Employee) -> dict:
        """
        Checks if a date is a holiday for an employee.
        Returns dict with keys: is_holiday (bool), description (str), is_ot_eligible (bool)
        Priority: Individual Holiday > Business Area Holiday > Company > Global
        """
        # 1. Get Employee Codes
        comp_code = employee.company.code if employee.company else None
        ba_code = employee.business_area.code if employee.business_area else None

        # 2. Check Business Area Holiday
        if ba_code:
            ba_holiday = session.query(HolidayCalendar).filter(
                HolidayCalendar.date == check_date,
                HolidayCalendar.business_area_code == ba_code
            ).first()
            if ba_holiday: return {"is_holiday": True, "description": ba_holiday.description, "is_ot_eligible": ba_holiday.is_ot_eligible}

        # 3. Check Company Holiday
        if comp_code:
            comp_holiday = session.query(HolidayCalendar).filter(
                HolidayCalendar.date == check_date,
                HolidayCalendar.company_code == comp_code
            ).first()
            if comp_holiday: return {"is_holiday": True, "description": comp_holiday.description, "is_ot_eligible": comp_holiday.is_ot_eligible}
            
        # 4. Global Holiday (if any, Null for all)
        global_holiday = session.query(HolidayCalendar).filter(
            HolidayCalendar.date == check_date,
            HolidayCalendar.company_code == None,
            HolidayCalendar.business_area_code == None
        ).first()
        if global_holiday: return {"is_holiday": True, "description": global_holiday.description, "is_ot_eligible": global_holiday.is_ot_eligible}
            
        return {"is_holiday": False, "description": "", "is_ot_eligible": False}

    @staticmethod
    def is_weekend(session: Session, check_date: date, employee: Employee) -> bool:
        """
        Checks if a date is a weekly holiday.
        """
        day_of_week = check_date.weekday()
        
        # 1. Employee Specific
        has_emp_config = session.query(WeeklyHoliday).filter_by(employee_id=employee.id).count() > 0
        if has_emp_config:
            return session.query(WeeklyHoliday).filter_by(employee_id=employee.id, day_of_week=day_of_week).count() > 0
            
        # 2. Business Area
        has_ba_config = session.query(WeeklyHoliday).filter_by(business_area_id=employee.business_area_id).count() > 0
        if has_ba_config:
            return session.query(WeeklyHoliday).filter_by(business_area_id=employee.business_area_id, day_of_week=day_of_week).count() > 0

        # 3. Company
        has_comp_config = session.query(WeeklyHoliday).filter_by(company_id=employee.company_id).count() > 0
        if has_comp_config:
            return session.query(WeeklyHoliday).filter_by(company_id=employee.company_id, day_of_week=day_of_week).count() > 0
            
        return False

    @staticmethod
    def get_month_stats(session: Session, month: int, year: int, employee: Employee):
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Fetch configs efficiently
        
        # Holidays
        comp_code = employee.company.code if employee.company else None
        ba_code = employee.business_area.code if employee.business_area else None

        # Global
        global_hols = session.query(HolidayCalendar).filter(
            HolidayCalendar.date >= start_date, HolidayCalendar.date <= end_date,
            HolidayCalendar.company_code == None, HolidayCalendar.business_area_code == None
        ).all()
        # Company
        comp_hols = []
        if comp_code:
            comp_hols = session.query(HolidayCalendar).filter(
                HolidayCalendar.date >= start_date, HolidayCalendar.date <= end_date,
                HolidayCalendar.company_code == comp_code
            ).all()
        # BA
        ba_hols = []
        if ba_code:
            ba_hols = session.query(HolidayCalendar).filter(
                HolidayCalendar.date >= start_date, HolidayCalendar.date <= end_date,
                HolidayCalendar.business_area_code == ba_code
            ).all()
        # Emp level removed from query
        
        # Merge (Priority Logic: Emp > BA > Comp > Global)
        # Note: Emp level removed
        holiday_dates = {} 
        for h in global_hols: holiday_dates[h.date] = h
        for h in comp_hols: holiday_dates[h.date] = h
        for h in ba_hols: holiday_dates[h.date] = h
        
        # Weekly Config
        emp_week_days = [w.day_of_week for w in session.query(WeeklyHoliday).filter_by(employee_id=employee.id).all()]
        ba_week_days = [w.day_of_week for w in session.query(WeeklyHoliday).filter_by(business_area_id=employee.business_area_id).all()]
        comp_week_days = [w.day_of_week for w in session.query(WeeklyHoliday).filter_by(company_id=employee.company_id).all()]
        
        effective_week_days = []
        if emp_week_days: effective_week_days = emp_week_days
        elif ba_week_days: effective_week_days = ba_week_days
        elif comp_week_days: effective_week_days = comp_week_days
        
        total_days = last_day
        holidays = 0
        weekends = 0
        
        current = start_date
        while current <= end_date:
            is_hol = current in holiday_dates
            is_wknd = current.weekday() in effective_week_days
            
            if is_hol: holidays += 1
            elif is_wknd: weekends += 1
                
            current += timedelta(days=1)
            
        working_days = total_days - holidays - weekends
        
        return {
            "total_days": total_days,
            "working_days": working_days,
            "holidays": holidays,
            "weekends": weekends
        }
