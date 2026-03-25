import os, glob, re

files = glob.glob('e:/attensync/salarySync/DeskTop_Version/ui/admin/*.py')
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    # 1. Add btn_neutral to the import if not exists
    if 'btn_refresh' in content and 'from ui.btn_styles import ' in content and 'btn_neutral' not in content:
        content = re.sub(r'(from ui\.btn_styles import.*)', r'\1, btn_neutral', content)

    # 2. Fix btn_refresh style
    content = re.sub(r'(btn_refresh\s*=\s*QPushButton\("Refresh"\))\s*(btn_refresh\.setStyleSheet\(btn_small_neutral\(\)\))?', r'\1\n        btn_refresh.setStyleSheet(btn_neutral())', content)
    content = re.sub(r'(btn_refresh\.setStyleSheet\(btn_neutral\(\)\)\s*)+', r'btn_refresh.setStyleSheet(btn_neutral())\n        ', content)

    # 3. Fix Layout ordering
    if 'header.addWidget(btn_refresh)' in content and 'header.addStretch()' in content:
        idx_stretch = content.find('header.addStretch()')
        idx_refresh = content.find('header.addWidget(btn_refresh)')
        
        if idx_refresh < idx_stretch:
            # Remove existing
            content = content.replace('        header.addWidget(btn_refresh)\n', '')
            content = content.replace('        header.addWidget(btn_refresh)', '')
            # Add after stretch
            content = content.replace('header.addStretch()', 'header.addStretch()\n        header.addWidget(btn_refresh)')
            
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
