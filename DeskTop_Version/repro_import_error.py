import sys
import os

sys.path.append(os.getcwd())
try:
    from services.legacy_import_service import LegacyImportService
except ImportError:
    pass

file_path = os.path.join("data", "Test_Import_Template.xlsx")

def run_import_test():
    print(f"Testing import with {file_path}")
    
    # We will try to test 'shifts' table as per user request
    tables_to_test = ["shifts"]
    
    for table in tables_to_test:
        print(f"\n--- Importing {table} ---")
        try:
            count, errors = LegacyImportService.import_table_data(file_path, table)
            print(f"Count: {count}")
            if errors:
                print("Errors found:")
                for e in errors:
                    print(f"  - {e}")
            else:
                print("Success: No errors.")
        except Exception as e:
            print(f"CRITICAL EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_import_test()
