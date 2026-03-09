import sqlite3

def migrate():
    # Connect to db
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()
    
    # Create payroll_records
    try:
        c.execute('''
            CREATE TABLE payroll_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                base_salary FLOAT NOT NULL DEFAULT 0.0,
                total_present FLOAT NOT NULL DEFAULT 0.0,
                total_absent FLOAT NOT NULL DEFAULT 0.0,
                total_leave FLOAT NOT NULL DEFAULT 0.0,
                total_holidays FLOAT NOT NULL DEFAULT 0.0,
                ot_hours FLOAT NOT NULL DEFAULT 0.0,
                ot_pay FLOAT NOT NULL DEFAULT 0.0,
                late_deduction FLOAT NOT NULL DEFAULT 0.0,
                leave_deduction FLOAT NOT NULL DEFAULT 0.0,
                net_salary FLOAT NOT NULL DEFAULT 0.0,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        ''')
        print("Created payroll_records table successfully.")
    except sqlite3.OperationalError as e:
        print(f"payroll_records error (maybe exists?): {e}")

    # Create bonus_records
    try:
        c.execute('''
            CREATE TABLE bonus_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                base_salary FLOAT NOT NULL DEFAULT 0.0,
                bonus_rate_or_amount FLOAT NOT NULL DEFAULT 0.0,
                is_percentage BOOLEAN NOT NULL DEFAULT 0,
                final_bonus_pay FLOAT NOT NULL DEFAULT 0.0,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        ''')
        print("Created bonus_records table successfully.")
    except sqlite3.OperationalError as e:
        print(f"bonus_records error (maybe exists?): {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
