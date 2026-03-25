import os, re

ADMIN_DIR = r'ui\admin'
files = [f for f in os.listdir(ADMIN_DIR) if f.endswith('.py')]

for fname in files:
    fpath = os.path.join(ADMIN_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    changed = False
    
    for i in range(len(lines)):
        line = lines[i]
        if 'horizontalHeader().setSectionResizeMode' in line:
            # e.g.: "        self.table_sub.horizontalHeader().setSectionResizeMode(...)"
            match = re.search(r'(\s*)(self\.[a-zA-Z0-9_]+)\.horizontalHeader', line)
            if match:
                indent = match.group(1)
                t_var = match.group(2)
                
                # Check next two lines to see if they are the erroneous self.table calls
                if i + 1 < len(lines) and 'self.table.verticalHeader().setDefaultSectionSize' in lines[i+1]:
                    if t_var != 'self.table':
                        lines[i+1] = f"{indent}{t_var}.verticalHeader().setDefaultSectionSize(36)"
                        changed = True
                if i + 2 < len(lines) and 'self.table.verticalHeader().hide()' in lines[i+2]:
                    if t_var != 'self.table':
                        lines[i+2] = f"{indent}{t_var}.verticalHeader().hide()"
                        changed = True
                        
    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Fixed table references in {fname}")

print("Done")
