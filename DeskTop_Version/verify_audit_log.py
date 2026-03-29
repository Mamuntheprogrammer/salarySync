from database import db
from models import Company, SystemLog
from utils.user_context import set_current_user_id
import json

def verify_audit():
    db.initialize()
    session = db.get_session()
    
    # Mock a user login
    set_current_user_id(999) # Using a test ID
    
    # Create a test company
    print("Creating a test company...")
    test_co = Company(code="TEST", name="Audit Test Co")
    session.add(test_co)
    session.commit()
    
    # Check if a log was created
    log = session.query(SystemLog).order_by(SystemLog.id.desc()).first()
    if log and log.entity_type == 'Company' and log.action_type == 'Created' and log.user_id == 999:
        print("SUCCESS: System log for Creation created!")
        print(f"Action: {log.action_type}")
        print(f"User ID: {log.user_id}")
        print(f"Details: {log.details}")
        
        # Now Update it
        print("\nUpdating company name...")
        test_co.name = "Updated Audit Test Co"
        session.commit()
        
        log = session.query(SystemLog).order_by(SystemLog.id.desc()).first()
        if log and log.action_type == 'Updated':
            print("SUCCESS: System log for Update created!")
            print(f"Details: {log.details}")
            
            # Now Delete it
            print("\nDeleting company...")
            session.delete(test_co)
            session.commit()
            
            log = session.query(SystemLog).order_by(SystemLog.id.desc()).first()
            if log and log.action_type == 'Deleted':
                print("SUCCESS: System log for Deletion created!")
            else:
                print("FAILURE: No log for Deletion found.")
        else:
            print("FAILURE: No log for Update found.")
    else:
        print("FAILURE: No log for Creation found.")

if __name__ == "__main__":
    verify_audit()
