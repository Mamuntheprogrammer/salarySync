import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, get_db_session
from models import Employee, Company, BusinessArea
from services.sync_service import SyncService
from config import Config
from sqlalchemy import create_engine, MetaData, Table, select

def run_test():
    print("--- Starting Remote Sync Verification ---")
    
    # 1. Setup Local DB with some data
    db.initialize()
    session = get_db_session()
    
    # Ensure some data exists
    if not session.query(Company).filter_by(code="EXIST").first():
        c = Company(code="EXIST", name="Existing Corp")
        session.add(c)
        session.commit()
    
    emp_count = session.query(Employee).count()
    print(f"Local Employees: {emp_count}")
    
    # 2. Define 'Remote' DB (just another sqlite file)
    remote_db_path = "remote_test.db"
    if os.path.exists(remote_db_path):
        os.remove(remote_db_path)
        
    remote_uri = f"sqlite:///{remote_db_path}"
    print(f"Mock Remote URI: {remote_uri}")
    
    # 3. Test Connection
    service = SyncService()
    success, msg = service.test_remote_connection(remote_uri)
    if success:
        print("[SUCCESS] Connection Test Passed")
    else:
        print(f"[FAILURE] Connection Test Failed: {msg}")
        return

    # 4. Trigger Sync (Initialize/Reset)
    print("Pushing data to remote (Reset=True)...")
    success, msg = service.push_to_remote_db(remote_uri, reset=True)
    
    if success:
        print(f"[SUCCESS] Sync Operation Reported Success: {msg}")
    else:
        print(f"[FAILURE] Sync Operation Failed: {msg}")
        return
        
    # 5. Verify Data in Remote
    remote_engine = create_engine(remote_uri)
    with remote_engine.connect() as conn:
        # Check tables exist
        meta = MetaData()
        meta.reflect(bind=remote_engine)
        
        if 'employees' in meta.tables:
            print("[SUCCESS] 'employees' table exists in remote")
            
            # Check count
            emp_table = meta.tables['employees']
            stmt = select(emp_table)
            result = conn.execute(stmt).fetchall()
            print(f"Remote Employees: {len(result)}")
            
            if len(result) == emp_count:
                print("[SUCCESS] Record count matches")
            else:
                print("[FAILURE] Record count mismatch")
        else:
            print("[FAILURE] 'employees' table missing in remote")

    # Cleanup
    if os.path.exists(remote_db_path):
        os.remove(remote_db_path)
        
    print("--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
