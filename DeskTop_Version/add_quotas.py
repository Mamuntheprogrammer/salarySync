from database import get_db_session
from models import LeaveQuota, Company, BusinessArea

session = get_db_session()
companies = session.query(Company).all()

leave_types = {
    "Sick": 10,
    "Casual": 10,
    "Unpaid": 30
}

for c in companies:
    print(f"Checking Company {c.code}...")
    for l_type, limit in leave_types.items():
        exists = session.query(LeaveQuota).filter_by(
            company_id=c.id, 
            leave_type=l_type, 
            year=2026 # Hardcoded for now based on service use of today().year
        ).first()
        
        if not exists:
            q = LeaveQuota(
                company_id=c.id,
                business_area_id=None,
                leave_type=l_type,
                quota_limit=limit,
                year=2026
            )
            session.add(q)
            print(f"  Added {l_type} quota.")
        else:
            print(f"  {l_type} exists.")
            
    # Also ensure Annual exists for 001 if missing
    if c.code == '001':
         exists = session.query(LeaveQuota).filter_by(company_id=c.id, leave_type="Annual", year=2026).first()
         if not exists:
             session.add(LeaveQuota(company_id=c.id, leave_type="Annual", quota_limit=14, year=2026))
             print("  Added Annual for 001")

session.commit()
print("Done.")
