import os
import glob
import re

for filepath in glob.glob("tests/test_*.py"):
    with open(filepath, "r") as f:
        content = f.read()
    
    new_content = re.sub(r'(\s+)manager\._save_evidence\(', r'\1await manager._save_evidence(', content)
    
    if new_content != content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
