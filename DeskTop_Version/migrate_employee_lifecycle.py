import os
import sys

# Ensure DeskTop_Version is in the path so we can import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import Config

def migrate():
    db_url = Config.get_db_url()
    print(f"Connecting to database at {db_url}...")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Checking for existing columns in employees table...")
        
        # Check if columns exist
        result = conn.execute(text("PRAGMA table_info(employees)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'valid_to' not in columns:
            print("Adding valid_to column...")
            conn.execute(text("ALTER TABLE employees ADD COLUMN valid_to DATE"))
        else:
            print("valid_to column already exists.")

        if 'resign_status' not in columns:
            print("Adding resign_status column...")
            conn.execute(text("ALTER TABLE employees ADD COLUMN resign_status VARCHAR(50)"))
        else:
            print("resign_status column already exists.")
            
        if 'resign_date' not in columns:
            print("Adding resign_date column...")
            conn.execute(text("ALTER TABLE employees ADD COLUMN resign_date DATE"))
        else:
            print("resign_date column already exists.")
            
        conn.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
