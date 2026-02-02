import sqlite3
import os

DB_FILE = "attensync.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("Starting migration: Making employees.company_id and business_area_id NULLABLE...")
    
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Rename existing table
        cursor.execute("ALTER TABLE employees RENAME TO employees_old")
        
        # 2. Create new table with NULLABLE columns
        # Note: We must ensure this schema matches models.py EXACTLY (except for the constraints we changed)
        create_sql = """
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            attendance_code VARCHAR(6) NOT NULL UNIQUE,
            full_name VARCHAR(100) NOT NULL,
            joining_date DATE,
            salary_base FLOAT,
            company_id INTEGER, 
            business_area_id INTEGER,
            designation_id INTEGER,
            designation_subcategory_id INTEGER,
            shift_id INTEGER,
            is_active BOOLEAN,
            custom_shift_start TIME,
            custom_shift_end TIME,
            FOREIGN KEY(company_id) REFERENCES companies(id),
            FOREIGN KEY(business_area_id) REFERENCES business_areas(id),
            FOREIGN KEY(designation_id) REFERENCES designations(id),
            FOREIGN KEY(designation_subcategory_id) REFERENCES designation_subcategories(id),
            FOREIGN KEY(shift_id) REFERENCES shifts(id)
        )
        """
        cursor.execute(create_sql)
        
        # 3. Copy Data
        # We assume columns match by name/order.
        cursor.execute("""
            INSERT INTO employees (id, attendance_code, full_name, joining_date, salary_base, company_id, 
                                   business_area_id, designation_id, designation_subcategory_id, shift_id, 
                                   is_active, custom_shift_start, custom_shift_end)
            SELECT id, attendance_code, full_name, joining_date, salary_base, company_id, 
                   business_area_id, designation_id, designation_subcategory_id, shift_id, 
                   is_active, custom_shift_start, custom_shift_end
            FROM employees_old
        """)
        
        # 4. Drop old table
        cursor.execute("DROP TABLE employees_old")
        
        conn.commit()
        print("Migration successful: Constraints relaxed.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        # Try to restore if possible? 
        # Actually if rollback works, we are good.
        # But if 'ALTER RENAME' committed... 
        # SQLite Transaction should cover DDL too.
    finally:
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.close()

if __name__ == "__main__":
    migrate()
