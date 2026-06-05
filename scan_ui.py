import os
import re

folder = r"c:\Users\DELL\Desktop\ai_tutor\templates"

for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(folder, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        # Find any text-gray-* without a dark:text-* in the same line
        # This is a heuristic, but helpful
        if re.search(r'text-gray-[789]00', line) and not re.search(r'dark:text-(white|gray|slate)', line):
            print(f"{filename}:{i+1} - Missing dark:text for {line.strip()[:80]}")
