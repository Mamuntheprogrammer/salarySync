import random
import string
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Employee, Company, BusinessArea
from database import get_db_session

class EmployeeService:
    @staticmethod
    def generate_attendance_code(session: Session) -> str:
        """Generates a unique 6-digit numeric code."""
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not session.query(Employee).filter_by(attendance_code=code).first():
                return code

    @staticmethod
    def create_employee(session: Session, data: dict) -> Employee:
        """
        Creates a new employee with auto-generated attendance code.
        data dict should contain:
        - full_name
        - designation
        - joining_date
        - salary_base
        - company_id
        - business_area_id
        - shift_id (optional)
        - custom_shift_start (optional)
        - custom_shift_end (optional)
        """
        
        # Generate code
        attendance_code = EmployeeService.generate_attendance_code(session)
        
        employee = Employee(
            attendance_code=attendance_code,
            full_name=data['full_name'],
            # designation=data.get('designation'), # Removed
            joining_date=data.get('joining_date'),
            salary_base=data.get('salary_base', 0.0),
            company_id=data['company_id'],
            business_area_id=data['business_area_id'],
            shift_id=data.get('shift_id'),
            designation_id=data.get('designation_id'),
            designation_subcategory_id=data.get('designation_subcategory_id'),
            is_active=data.get('is_active', True),
            custom_shift_start=data.get('custom_shift_start'),
            custom_shift_end=data.get('custom_shift_end')
        )
        
        session.add(employee)
        session.commit()
        return employee

    @staticmethod
    def update_employee(session: Session, employee_id: int, data: dict) -> Employee:
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
            
        for key, value in data.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
                
        session.commit()
        return employee
        
    @staticmethod
    def delete_employee(session: Session, employee_id: int):
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if employee:
            session.delete(employee)
            session.commit()
            return True
        return False

    @staticmethod
    def get_employee_by_code(session: Session, code: str) -> Employee:
        return session.query(Employee).filter_by(attendance_code=code).first()

    @staticmethod
    def get_all_employees(session: Session, company_id=None):
        query = session.query(Employee)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.all()
