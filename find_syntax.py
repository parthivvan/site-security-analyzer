import os
import glob
import re

src_dir = r"c:\Users\Parthiv Vanapalli\Desktop\site-security-analyzer\frontend\src"

files = glob.glob(os.path.join(src_dir, "**/*.jsx"), recursive=True)
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '?' in line and '}' in line and ':' not in line.split('?')[1]:
            # This is a naive check but might catch missing false branches
            print(f"{os.path.basename(filepath)}:{i+1} -> {line.strip()}")
