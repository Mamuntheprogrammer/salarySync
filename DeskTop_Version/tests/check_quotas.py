from database import get_db_session
from models import LeaveQuota, Company, BusinessArea

session = get_db_session()
quotas = session.query(LeaveQuota).all()

print(f"Total Quotas found: {len(quotas)}")
for q in quotas:
    c_code = q.company.code if q.company else "None"
    ba_code = q.business_area.code if q.business_area else "None"
    print(f"ID: {q.id} | Year: {q.year} | Type: {q.leave_type} | Limit: {q.quota_limit} | Comp: {c_code} | BA: {ba_code}")
