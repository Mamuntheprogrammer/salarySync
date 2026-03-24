from sqlalchemy.orm import Session
from models import Shift, Employee
from datetime import datetime, time

class ShiftService:
    @staticmethod
    def create_shift(session: Session, name: str, start_time: time, end_time: time,
                     late_allowance: int = 15, company_id=None, business_area_id=None) -> Shift:
        shift = Shift(
            name=name,
            start_time=start_time,
            end_time=end_time,
            late_allowance_minutes=late_allowance,
            company_id=company_id,
            business_area_id=business_area_id,
        )
        session.add(shift)
        session.commit()
        return shift
        
    @staticmethod
    def get_all_shifts(session: Session, company_id=None, business_area_id=None):
        """Return shifts scoped to the given company/BA plus any global (unscoped) shifts."""
        from sqlalchemy import or_
        q = session.query(Shift)
        if company_id is not None:
            q = q.filter(
                or_(Shift.company_id == None, Shift.company_id == company_id)
            )
        if business_area_id is not None:
            q = q.filter(
                or_(Shift.business_area_id == None, Shift.business_area_id == business_area_id)
            )
        return q.order_by(Shift.name).all()
        
    @staticmethod
    def assign_shift_to_employee(session: Session, employee_id: int, shift_id: int = None, custom_start: time = None, custom_end: time = None):
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
            
        if shift_id:
            employee.shift_id = shift_id
            employee.custom_shift_start = None
            employee.custom_shift_end = None
        elif custom_start and custom_end:
            employee.shift_id = None
            employee.custom_shift_start = custom_start
            employee.custom_shift_end = custom_end
        else:
            raise ValueError("Either shift_id or custom shift times must be provided")
            
        session.commit()
        return employee
        
    @staticmethod
    def get_employee_shift_details(employee: Employee):
        """Returns effective shift details (start_time, end_time, late_allowance)"""
        if employee.shift_id and employee.shift:
            return {
                "name": employee.shift.name,
                "start_time": employee.shift.start_time,
                "end_time": employee.shift.end_time,
                "late_allowance": employee.shift.late_allowance_minutes,
                "is_custom": False
            }
        elif employee.custom_shift_start and employee.custom_shift_end:
             return {
                "name": "Custom Shift",
                "start_time": employee.custom_shift_start,
                "end_time": employee.custom_shift_end,
                "late_allowance": 15, # Default for custom shifts or make configurable?
                "is_custom": True
            }
        return None
