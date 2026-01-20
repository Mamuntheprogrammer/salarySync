import pandas as pd
import sys

file_path = 'e:/attensync/salarySync/shopmanager/sample_data.xlsx'
try:
    xl = pd.ExcelFile(file_path)
    print("Sheet names:", xl.sheet_names)
    
    if xl.sheet_names:
        first_sheet = xl.sheet_names[0]
        print(f"\n--- First Sheet: {first_sheet} ---")
        df = xl.parse(first_sheet)
        print("Columns:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head().to_string())
        
        # Check dtypes
        print("\nData Types:")
        print(df.dtypes)
except Exception as e:
    print(f"Error reading excel: {e}")
