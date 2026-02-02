from database import get_db_session, db
from sqlalchemy import text

def migrate():
    session = get_db_session()
    try:
        # Check if column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(payroll_config)"))
            columns = [row[1] for row in result]
            
            if 'late_days_penalty_threshold' not in columns:
                print("Adding late_days_penalty_threshold column...")
                conn.execute(text("ALTER TABLE payroll_config ADD COLUMN late_days_penalty_threshold INTEGER DEFAULT 3"))
                conn.commit()
                print("Column added.")
            else:
                print("Column late_days_penalty_threshold already exists.")
                
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
