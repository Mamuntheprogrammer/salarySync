from database import get_db_session, db
from sqlalchemy import text

def migrate():
    # Initialize DB engine properly via existing logic
    db.initialize()
    
    with db.engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE employees ADD COLUMN face_encoding_path VARCHAR(500) NULL'))
            conn.commit()
            print("Added face_encoding_path to employees successfully.")
        except Exception as e:
            print(f"Migration error (column might already exist): {e}")

if __name__ == '__main__':
    migrate()
