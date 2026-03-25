import os, glob, re

files_to_fix = [
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/admin_terminal.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/backup_settings.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/setup/cloud_setup.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/terminal/employee_terminal.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/face_manager.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/import_module.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/legacy_import.py',
    'e:/attensync/salarySync/DeskTop_Version/ui/admin/reports.py'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add imports. Just prepend to the file safely.
    if 'from ui.btn_styles import' not in content:
        content = 'from ui.btn_styles import btn_primary, btn_neutral, btn_danger\n' + content
    else:
        # Just ensure btn_danger is there if it already imports something
        if 'btn_danger' not in content: content = content.replace('from ui.btn_styles import ', 'from ui.btn_styles import btn_danger, ')
        if 'btn_primary' not in content: content = content.replace('from ui.btn_styles import ', 'from ui.btn_styles import btn_primary, ')
        if 'btn_neutral' not in content: content = content.replace('from ui.btn_styles import ', 'from ui.btn_styles import btn_neutral, ')

    # 2. Replace hardcoded inline CSS with mapped btn styles.
    content = re.sub(r'([A-Za-z0-9_.]+)\.setStyleSheet\("background-color: \#4CAF50.*?"\)', r'\1.setStyleSheet(btn_primary())', content)
    content = re.sub(r'([A-Za-z0-9_.]+)\.setStyleSheet\("background-color: \#f44336.*?"\)', r'\1.setStyleSheet(btn_danger())', content)
    content = re.sub(r'([A-Za-z0-9_.]+)\.setStyleSheet\("background-color: \#2196F3.*?"\)', r'\1.setStyleSheet(btn_primary())', content)
    content = re.sub(r'([A-Za-z0-9_.]+)\.setStyleSheet\("background-color: \#9E9E9E.*?"\)', r'\1.setStyleSheet(btn_neutral())', content)
    content = re.sub(r'([A-Za-z0-9_.]+)\.setStyleSheet\("background-color: \#E91E63.*?"\)', r'\1.setStyleSheet(btn_primary())', content)

    # 3. For reports.py and legacy_import.py, if buttons don't have setStyleSheet already, add them
    # Match patterns like: btn_generate = QPushButton("Generate")
    # Replace with: btn_generate = QPushButton("Generate")\n        btn_generate.setStyleSheet(btn_primary())
    # But only if not already styled.
    
    def inject_style(match):
        var = match.group(1)
        btn_text = match.group(2)
        full_line = match.group(0)
        
        # Decide style
        style = "btn_primary()"
        if btn_text.lower() in ["cancel", "reset", "clear", "clear selection", "browse", "select file...", "export csv", "download template"]:
            style = "btn_neutral()"
            
        return f'{full_line}\n        {var}.setStyleSheet({style})'

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        m = re.search(r'([a-zA-Z0-9_.]+)\s*=\s*QPushButton\("(.*?)"\)', line)
        if m:
            var = m.group(1).split('.')[-1] # self.btn -> btn
            # Look ahead to see if it's already styled
            already_styled = False
            for j in range(1, 4):
                if i + j < len(lines) and (f'{var}.setStyleSheet' in lines[i+j] or f'{m.group(1)}.setStyleSheet' in lines[i+j]):
                    already_styled = True
                    break
            
            if not already_styled:
                style = "btn_primary()"
                btn_text = m.group(2).lower()
                if any(x in btn_text for x in ["cancel", "reset", "clear", "browse", "select file", "export", "download template"]):
                    style = "btn_neutral()"
                
                # compute indentation
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(line)
                new_lines.append(f'{indent}{m.group(1)}.setStyleSheet({style})')
                i += 1
                continue
                
        new_lines.append(line)
        i += 1
        
    content = '\n'.join(new_lines)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print(f"Cleaned {os.path.basename(filepath)}")

