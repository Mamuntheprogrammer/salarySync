import sqlite3
import os

DB_FILE = os.path.join("data", "attensync_v3.db")

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("Starting migration: Making payroll_config.company_id NULLABLE...")
    
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Rename existing table
        cursor.execute("ALTER TABLE payroll_config RENAME TO payroll_config_old")
        
        # 2. Create new table with NULLABLE company_id
        create_sql = """
        CREATE TABLE payroll_config (
            id INTEGER PRIMARY KEY,
            company_id INTEGER UNIQUE,
            ot_rate_multiplier FLOAT,
            holiday_ot_rate_multiplier FLOAT,
            late_deduction_multiplier FLOAT,
            short_leave_deduction_multiplier FLOAT,
            late_days_penalty_threshold INTEGER,
            calculate_salary_on_present_days BOOLEAN,
            use_actual_days_in_month BOOLEAN,
            days_in_month_calculation INTEGER,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        """
        cursor.execute(create_sql)
        
        # 3. Copy Data
        cursor.execute("""
            INSERT INTO payroll_config (id, company_id, ot_rate_multiplier, holiday_ot_rate_multiplier, 
                                        late_deduction_multiplier, short_leave_deduction_multiplier, 
                                        late_days_penalty_threshold, calculate_salary_on_present_days, 
                                        use_actual_days_in_month, days_in_month_calculation)
            SELECT id, company_id, ot_rate_multiplier, holiday_ot_rate_multiplier, 
                   late_deduction_multiplier, short_leave_deduction_multiplier, 
                   late_days_penalty_threshold, calculate_salary_on_present_days, 
                   use_actual_days_in_month, days_in_month_calculation
            FROM payroll_config_old
        """)
        
        # 4. Drop old table
        cursor.execute("DROP TABLE payroll_config_old")
        
        conn.commit()
        print("Migration successful: payroll_config.company_id is now nullable.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.close()

if __name__ == "__main__":
    migrate()
