from database import get_db_session
from models import Attendance
import sys

session = get_db_session()
att = session.query(Attendance).order_by(Attendance.id.desc()).all()
for a in att[:5]:
    try:
        emp_name = a.employee.full_name if a.employee else "Unknown"
        print(f"ID={a.id}, Emp={emp_name}, Date={a.date}, In={a.clock_in}, Out={a.clock_out}")
    except Exception as e:
        print(f"Error {e}")
