from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(4), unique=True, nullable=False)  # 4-digit code
    name = Column(String(100), nullable=False)
    
    # Relationships
    business_areas = relationship("BusinessArea", back_populates="company", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="company")

class BusinessArea(Base):
    __tablename__ = 'business_areas'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(2), nullable=False)  # 2-digit code
    name = Column(String(100), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="business_areas")
    employees = relationship("Employee", back_populates="business_area")

class Designation(Base):
    __tablename__ = 'designations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    subcategories = relationship("DesignationSubcategory", back_populates="designation", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="designation")

class DesignationSubcategory(Base):
    __tablename__ = 'designation_subcategories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    designation_id = Column(Integer, ForeignKey('designations.id'), nullable=False)
    
    # Relationships
    designation = relationship("Designation", back_populates="subcategories")
    employees = relationship("Employee", back_populates="designation_subcategory")

class Shift(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    late_allowance_minutes = Column(Integer, default=15)

    # Scope (nullable = global / applies across all companies/areas)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    business_area_id = Column(Integer, ForeignKey('business_areas.id'), nullable=True)

    # Relationships
    employees = relationship("Employee", back_populates="shift")
    company = relationship("Company", foreign_keys=[company_id])
    business_area = relationship("BusinessArea", foreign_keys=[business_area_id])


class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    # designation = Column(String(100)) # Deprecated
    joining_date = Column(Date, default=datetime.now)
    salary_base = Column(Float, default=0.0)
    
    # Face Recognition
    face_encoding_path = Column(String(500), nullable=True)
    
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    business_area_id = Column(Integer, ForeignKey('business_areas.id'), nullable=True)
    
    designation_id = Column(Integer, ForeignKey('designations.id'), nullable=True)
    designation_subcategory_id = Column(Integer, ForeignKey('designation_subcategories.id'), nullable=True)
    
    # Shift assignment (Null means custom shift or no shift assigned yet)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=True)
    
    # Custom Shift Override (if shift_id is None)
    is_active = Column(Boolean, default=True)
    custom_shift_start = Column(Time, nullable=True)
    custom_shift_end = Column(Time, nullable=True)
    
    # Lifecycle Management
    valid_to = Column(Date, nullable=True)
    resign_status = Column(String(50), nullable=True) # Resigned, Terminated, etc.
    resign_date = Column(Date, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="employees")
    business_area = relationship("BusinessArea", back_populates="employees")
    designation = relationship("Designation", back_populates="employees")
    designation_subcategory = relationship("DesignationSubcategory", back_populates="employees")
    shift = relationship("Shift", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leaves = relationship("ShortLeave", back_populates="employee", cascade="all, delete-orphan")
    bonuses = relationship("Bonus", back_populates="employee", cascade="all, delete-orphan")
    salary_breakdowns = relationship("SalaryBreakdown", back_populates="employee", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, nullable=False, default=datetime.now)
    
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)
    
    # Calculated Fields
    # Calculated Fields
    # duty_time_hours, overtime_hours, short_leave_hours removed as per request
    # duty_time_hours, overtime_hours, short_leave_hours, late_hours removed as per request
    
    is_holiday_ot = Column(Boolean, default=False)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

class ShortLeave(Base):
    __tablename__ = 'short_leaves'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, nullable=False, default=datetime.now)
    
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String(200))
    status = Column(String(20), default="Pending") # Pending, Approved, Rejected
    
    # Relationships
    employee = relationship("Employee", back_populates="leaves")

class HolidayCalendar(Base):
    __tablename__ = 'holydays_calender'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)
    is_ot_eligible = Column(Boolean, default=False)
    year = Column(Integer, nullable=False)
    type = Column(String(50), default="National") # National, Festival, etc.
    
    # Levels of granular control
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    business_area_id = Column(Integer, ForeignKey('business_areas.id'), nullable=True)
    
    # Relationships
    company = relationship("Company")
    business_area = relationship("BusinessArea")

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    leave_type = Column(String(50), nullable=False) # Sick, Annual, Casual
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    request_date = Column(Date, nullable=False)
    reason = Column(String(200))
    status = Column(String(20), default="Pending") # Pending, Approved, Rejected
    rejection_reason = Column(String(200), nullable=True)
    
    # Relationship
    employee = relationship("Employee")

class WeeklyHoliday(Base):
    __tablename__ = 'weekly_holidays'
    
    id = Column(Integer, primary_key=True)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    business_area_id = Column(Integer, ForeignKey('business_areas.id'), nullable=True)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=True)
    
    # Relationships
    company = relationship("Company")
    business_area = relationship("BusinessArea")
    shift = relationship("Shift")

class LeaveQuota(Base):
    __tablename__ = 'leave_quotas'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    leave_type = Column(String(50), default="ShortLeave") # ShortLeave (Hours), SickLeave (Days), etc.
    quota_limit = Column(Float, default=0.0) # Hours or Days depending on type
    
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    business_area_id = Column(Integer, ForeignKey('business_areas.id'), nullable=True) 
    
    # Relationships
    company = relationship("Company")
    business_area = relationship("BusinessArea")

class PayrollConfig(Base):
    __tablename__ = 'payroll_config'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), unique=True, nullable=True)
    
    # Rates
    ot_rate_multiplier = Column(Float, default=1.5) # x times hourly rate
    holiday_ot_rate_multiplier = Column(Float, default=2.0) # x times hourly rate
    
    # Deductions
    late_deduction_multiplier = Column(Float, default=1.0) # x times hourly rate per hour late    
    short_leave_deduction_multiplier = Column(Float, default=1.0) # x times hourly rate per hour
    late_days_penalty_threshold = Column(Integer, default=3) # e.g. 3 days late -> 1 day salary cut
    
    # Logic Settings
    calculate_salary_on_present_days = Column(Boolean, default=True) # If True, Pay = Daily Rate * Present Days. If False, Pay = Base - Deductions
    use_actual_days_in_month = Column(Boolean, default=False) # If True, daily rate = Base / Actual Days
    days_in_month_calculation = Column(Integer, default=30) # Fixed 30 or actual? Fixed 30 is simpler.

    company = relationship("Company")

class AdminUser(Base):
    __tablename__ = 'admin_users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="admin") # admin, user
    
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    employee = relationship("Employee")

class Bonus(Base):
    __tablename__ = 'bonuses'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    is_percentage = Column(Boolean, default=False, nullable=False)
    description = Column(String(200), nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="bonuses")

class PayrollRecord(Base):
    __tablename__ = 'payroll_records'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Snapshot data
    base_salary = Column(Float, nullable=False, default=0.0)
    total_present = Column(Float, nullable=False, default=0.0)
    total_absent = Column(Float, nullable=False, default=0.0)
    total_leave = Column(Float, nullable=False, default=0.0)
    total_holidays = Column(Float, nullable=False, default=0.0)
    
    ot_hours = Column(Float, nullable=False, default=0.0)
    ot_pay = Column(Float, nullable=False, default=0.0)
    
    late_deduction = Column(Float, nullable=False, default=0.0)
    leave_deduction = Column(Float, nullable=False, default=0.0)
    
    net_salary = Column(Float, nullable=False, default=0.0)
    
    # Audit logic
    generated_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")

class BonusRecord(Base):
    __tablename__ = 'bonus_records'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Snapshot data
    base_salary = Column(Float, nullable=False, default=0.0)
    bonus_rate_or_amount = Column(Float, nullable=False, default=0.0)
    is_percentage = Column(Boolean, nullable=False, default=False)
    
    final_bonus_pay = Column(Float, nullable=False, default=0.0)
    
    # Audit logic
    generated_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")

class SalaryBreakdown(Base):
    __tablename__ = 'salary_breakdowns'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    year = Column(Integer, nullable=False)
    valid_to = Column(Date, nullable=True)
    
    basic = Column(Float, nullable=False, default=0.0)
    house_rent_allowance = Column(Float, nullable=False, default=0.0)
    conveyance = Column(Float, nullable=False, default=0.0)
    medical = Column(Float, nullable=False, default=0.0)
    mobile_bill = Column(Float, nullable=False, default=0.0)
    transportation_allowance = Column(Float, nullable=False, default=0.0)
    other_allowance = Column(Float, nullable=False, default=0.0)
    
    # Relationships
    employee = relationship("Employee", back_populates="salary_breakdowns")
