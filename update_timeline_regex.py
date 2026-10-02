import os
import glob
import re

files = glob.glob('*.md') + glob.glob('*.html')

for filepath in files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    original = content
    
    content = re.sub(r"In April 2026, HMRC's Making Tax Digital \(MTD\) mandate comes into full force", "HMRC's MTD Phase 1 mandate went live 5 months ago. Phase 2 hits in April 2027", content)
    content = re.sub(r"In April 2026, HMRC's Making Tax Digital \(MTD\) mandate comes into full statutory effect", "HMRC's MTD Phase 1 mandate went live 5 months ago. Phase 2 hits in April 2027", content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Regex updated {filepath}")
