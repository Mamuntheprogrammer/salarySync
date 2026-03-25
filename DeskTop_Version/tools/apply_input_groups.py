import os, re

files = [
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/reports.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/setup/cloud_setup.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/calendar_management.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/backup_settings.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/shift_management.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/business_area_management.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/print_documents.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/bonus_run_module.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/payroll_module.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/payroll_config_management.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/attendance_maintenance.py'
]

for filepath in files:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # Needs import
    if 'from ui.custom_widgets import make_input_group' not in content:
        content = 'from ui.custom_widgets import make_input_group\n' + content

    # Regex to find: form.addRow("Label", widget)
    # We want to replace it with: form.addRow(make_input_group("Label", widget))
    # Be careful, sometimes it's `layout.addRow(...)`
    # Match: ([a-zA-Z0-9_]+)\.addRow\(\s*("[^"]+")\s*,\s*([a-zA-Z0-9_.]+)\s*\)
    # Be careful NOT to match if it already has make_input_group
    
    def replacer(match):
        form_var = match.group(1)
        label_text = match.group(2)
        widget_var = match.group(3)
        return f'{form_var}.addRow(make_input_group({label_text}, {widget_var}))'
        
    content = re.sub(r'([a-zA-Z0-9_]+)\.addRow\(\s*("[^"]+")\s*,\s*([a-zA-Z0-9_.]+)\s*\)', replacer, content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored input groups in {os.path.basename(filepath)}")
