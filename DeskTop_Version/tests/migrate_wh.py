import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
try:
    from database import db, Base
except ImportError:
    pass

def migrate():
    print("Migrating Weekly Holidays Table...")
    # Initialize DB to get engine
    db.initialize()
    engine = db.engine
    
    # 1. Drop old table
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS weekly_holidays"))
        conn.commit()
        print("Dropped 'weekly_holidays' table.")
        
    # 2. Re-create tables
    Base.metadata.create_all(engine)
    print("Re-created tables.")

if __name__ == "__main__":
    migrate()
