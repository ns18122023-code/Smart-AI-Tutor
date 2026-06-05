import os

filepath = r"c:\Users\DELL\Desktop\ai_tutor\templates\auth.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Wrapper
content = content.replace(
    'bg-primary relative overflow-hidden',
    'bg-gray-50 dark:bg-primary relative overflow-hidden transition-colors duration-300'
)

# Card
content = content.replace(
    'bg-white dark:bg-slate-800/10 backdrop-blur-xl border border-white/20',
    'bg-white dark:bg-slate-800/20 backdrop-blur-xl border border-gray-200 dark:border-white/10'
)

# Text Colors
content = content.replace('text-white tracking-tight', 'text-gray-800 dark:text-white tracking-tight')
content = content.replace('text-gray-300 mt-2', 'text-gray-500 dark:text-gray-300 mt-2')

# Labels
content = content.replace('text-gray-200 mb-1', 'text-gray-700 dark:text-gray-200 mb-1')
content = content.replace('text-gray-200">Password', 'text-gray-700 dark:text-gray-200">Password')

# Inputs
content = content.replace(
    'bg-white dark:bg-slate-800/5 border border-white/10 rounded-lg text-white',
    'bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-800 dark:text-white'
)

# Footer Text
content = content.replace('text-gray-300 text-sm mt-6', 'text-gray-600 dark:text-gray-300 text-sm mt-6')
content = content.replace('hover:text-white transition', 'hover:text-gray-800 dark:hover:text-white transition')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("auth.html fixed!")
