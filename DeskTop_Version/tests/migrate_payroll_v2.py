from database import get_db_session, db
from sqlalchemy import text

def migrate():
    session = get_db_session()
    try:
        # Check if column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(payroll_config)"))
            columns = [row[1] for row in result]
            
            if 'use_actual_days_in_month' not in columns:
                print("Adding use_actual_days_in_month column...")
                conn.execute(text("ALTER TABLE payroll_config ADD COLUMN use_actual_days_in_month BOOLEAN DEFAULT 0"))
                conn.commit()
                print("Column added.")
            else:
                print("Column use_actual_days_in_month already exists.")
                
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
