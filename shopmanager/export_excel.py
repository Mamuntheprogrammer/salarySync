# import sqlite3
# import pandas as pd

# # -------- CONFIG --------
# DB_PATH = "db.sqlite3"      # path to sqlite db
# OUTPUT_EXCEL = "exported_data.xlsx"
# # ------------------------

# # Connect to SQLite
# conn = sqlite3.connect(DB_PATH)

# # Get all table names
# tables = pd.read_sql(
#     "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
#     conn
# )

# # Create Excel writer
# with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
#     for table_name in tables["name"]:
#         df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
#         df.to_excel(writer, sheet_name=table_name[:31], index=False)
#         print(f"Exported table: {table_name}")

# # Close DB connection
# conn.close()

# print("✅ Export completed successfully")
import os
print(os.environ.get("pass1"))
