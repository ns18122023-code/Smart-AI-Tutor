import os
import re

templates_dir = r"c:\Users\DELL\Desktop\ai_tutor\templates"

replacements = [
    (r'(?<!dark:)bg-white', r'bg-white dark:bg-slate-800'),
    (r'(?<!dark:)bg-gray-50(?!/)', r'bg-gray-50 dark:bg-slate-900'),
    (r'(?<!dark:)bg-gray-100', r'bg-gray-100 dark:bg-slate-700'),
    
    (r'(?<!dark:)border-gray-100', r'border-gray-100 dark:border-slate-700'),
    (r'(?<!dark:)border-gray-200', r'border-gray-200 dark:border-slate-700'),
    (r'(?<!dark:)border-gray-300', r'border-gray-300 dark:border-slate-600'),
    
    (r'(?<!dark:)text-gray-800', r'text-gray-800 dark:text-white'),
    (r'(?<!dark:)text-gray-700', r'text-gray-700 dark:text-gray-200'),
    (r'(?<!dark:)text-gray-600', r'text-gray-600 dark:text-gray-300'),
    (r'(?<!dark:)text-gray-500', r'text-gray-500 dark:text-gray-400'),
    (r'(?<!dark:)text-gray-900', r'text-gray-900 dark:text-white'),
    
    (r'(?<!dark:)hover:bg-gray-50(?!/)', r'hover:bg-gray-50 dark:hover:bg-slate-700'),
    (r'(?<!dark:)hover:bg-gray-100', r'hover:bg-gray-100 dark:hover:bg-slate-600'),
    (r'(?<!dark:)hover:text-gray-900', r'hover:text-gray-900 dark:hover:text-white'),
    
    # prose
    (r'(?<!dark:)prose(?!-)', r'prose dark:prose-invert'),
]

for filename in os.listdir(templates_dir):
    if filename.endswith(".html") and filename != "base.html":
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for pattern, replacement in replacements:
            # We use regex to replace but avoid replacing if the replacement is already there
            # actually our lookbehind handles basic cases, but wait, the lookbehind (?<!dark:) 
            # won't prevent `bg-white dark:bg-slate-800` from being replaced on `bg-white` 
            # because `bg-white` isn't preceded by `dark:`. It's preceded by space!
            # So if it's already "bg-white dark:bg-slate-800", matching "bg-white" will 
            # turn it into "bg-white dark:bg-slate-800 dark:bg-slate-800".
            # We need to make sure we don't replace if `dark:` is right after.
            pass
            
        # Let's do it safely:
        for old, new_class in replacements:
            # old is something like `(?<!dark:)bg-white`
            # we want to match `bg-white` not followed by ` dark:bg-slate-800`
            # since `old` is regex string, let's just use string replace but very carefully
            # actually, since we are doing this once, string replace is fine, but we might duplicate if we run twice.
            pass
            
def safe_replace(content, cls_to_find, dark_cls_to_add):
    # Find `cls_to_find`, if it's inside class="...", and doesn't already have `dark_cls_to_add`
    # A simple way for a one-off script: just replace `cls_to_find` with `cls_to_find dark_cls_to_add`
    # and then clean up duplicates `dark_cls_to_add dark_cls_to_add` -> `dark_cls_to_add`
    temp = content.replace(cls_to_find, f"{cls_to_find} {dark_cls_to_add}")
    # clean duplicates
    temp = temp.replace(f"{dark_cls_to_add} {dark_cls_to_add}", dark_cls_to_add)
    return temp

simple_reps = [
    ('bg-white', 'dark:bg-slate-800'),
    ('bg-gray-50 ', 'dark:bg-slate-900 '),
    ('bg-gray-50"', 'dark:bg-slate-900"'),
    ('bg-gray-50<', 'dark:bg-slate-900<'),
    ('bg-gray-100', 'dark:bg-slate-700'),
    
    ('border-gray-100', 'dark:border-slate-700'),
    ('border-gray-200', 'dark:border-slate-700'),
    ('border-gray-300', 'dark:border-slate-600'),
    
    ('text-gray-800', 'dark:text-white'),
    ('text-gray-700', 'dark:text-gray-200'),
    ('text-gray-600', 'dark:text-gray-300'),
    ('text-gray-500', 'dark:text-gray-400'),
    ('text-gray-900', 'dark:text-white'),
    
    ('hover:bg-gray-50 ', 'dark:hover:bg-slate-700 '),
    ('hover:bg-gray-50"', 'dark:hover:bg-slate-700"'),
    ('hover:bg-gray-100', 'dark:hover:bg-slate-600'),
    ('hover:text-gray-900', 'dark:hover:text-white'),
    
    (' prose ', ' prose dark:prose-invert '),
    ('"prose ', '"prose dark:prose-invert '),
    ('from-blue-50', 'dark:from-slate-800'),
    ('to-indigo-50', 'dark:to-slate-800'),
    ('from-red-50', 'dark:from-slate-800'),
    ('to-orange-50', 'dark:to-slate-800'),
    ('border-blue-100', 'dark:border-slate-700'),
    ('border-red-100', 'dark:border-slate-700'),
]

for filename in os.listdir(templates_dir):
    if filename.endswith(".html") and filename != "base.html":
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old, dark_cls in simple_reps:
            content = safe_replace(content, old, dark_cls)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("Theme update complete.")
