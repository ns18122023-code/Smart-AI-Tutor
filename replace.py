import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add MOCK_DB at the top, right after imports
if 'MOCK_DB =' not in content:
    content = re.sub(
        r'(import datetime\n)',
        r'\1\n# Global in-memory storage to bypass Flask 4KB cookie limit in mock mode\nMOCK_DB = {\n    "bookmarks": {},\n    "activities": {},\n    "tasks": {},\n    "stats": {},\n    "quizzes": {}\n}\n',
        content
    )

# Replace get_mock_bookmarks
old_get_bookmarks = '''def get_mock_bookmarks():
    uid = get_user_id()
    key = f"mock_bookmarks_{uid}"
    if key not in session:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            session[key] = [
                {'id': 'bm-1', 'title': 'SQL Joins Cheatsheet', 'type': 'concept', 'content': 'SQL joins are used to combine rows from two or more tables based on a related column between them. Types include INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN.', 'created_at': '3 hours ago'}, 
                {'id': 'bm-2', 'title': 'OS Deadlock explanation', 'type': 'chat', 'content': 'A deadlock occurs when a set of processes are blocked because each process is holding a resource and waiting for another resource held by some other process in the set.', 'created_at': 'Yesterday'},
                {'id': 'bm-3', 'title': 'Summary: Introduction to Operating Systems', 'type': 'pdf', 'content': '<h1>Introduction to Operating Systems</h1><p>An Operating System (OS) is software that acts as an interface between computer hardware components and the user. Every computer system must have at least one operating system to run other programs.</p><h3>Key Functions</h3><ul><li><strong>Resource Management:</strong> Manages CPU time, memory, storage, and I/O devices.</li><li><strong>File System Control:</strong> Controls how data is stored and retrieved.</li><li><strong>Security:</strong> Protects system data and resources from unauthorized access.</li></ul>', 'created_at': '2 days ago'}
            ]
        else:
            # Premium starter bookmarks for brand-new users, so they see exactly where items show up out of the box!
            session[key] = [
                {'id': 'bm-1', 'title': 'Guide: Getting Started with AI Tutor', 'type': 'concept', 'content': '<h1>Getting Started</h1><p>Welcome to your personal AI Tutor space! You can ask questions about code, database queries, operating systems, or engineering. Your study streak increases each calendar day you engage in learning.</p>', 'created_at': 'Just now'},
                {'id': 'bm-2', 'title': 'Summary: AI Tutor Platform Guide', 'type': 'pdf', 'content': '<h1>AI Tutor Platform Guide</h1><p>The Smart AI Tutor platform includes advanced PDF Summarization, Quiz Generation, true calendar-based study streaks, and dynamic weakness detection. Click the Bookmark icon on any summary to save it here in real-time.</p>', 'created_at': 'Just now'}
            ]
    return session[key]'''

new_get_bookmarks = '''def get_mock_bookmarks():
    uid = get_user_id()
    if uid not in MOCK_DB["bookmarks"]:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            MOCK_DB["bookmarks"][uid] = [
                {'id': 'bm-1', 'title': 'SQL Joins Cheatsheet', 'type': 'concept', 'content': 'SQL joins are used to combine rows from two or more tables based on a related column between them. Types include INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN.', 'created_at': '3 hours ago'}, 
                {'id': 'bm-2', 'title': 'OS Deadlock explanation', 'type': 'chat', 'content': 'A deadlock occurs when a set of processes are blocked because each process is holding a resource and waiting for another resource held by some other process in the set.', 'created_at': 'Yesterday'},
                {'id': 'bm-3', 'title': 'Summary: Introduction to Operating Systems', 'type': 'pdf', 'content': '<h1>Introduction to Operating Systems</h1><p>An Operating System (OS) is software that acts as an interface between computer hardware components and the user. Every computer system must have at least one operating system to run other programs.</p><h3>Key Functions</h3><ul><li><strong>Resource Management:</strong> Manages CPU time, memory, storage, and I/O devices.</li><li><strong>File System Control:</strong> Controls how data is stored and retrieved.</li><li><strong>Security:</strong> Protects system data and resources from unauthorized access.</li></ul>', 'created_at': '2 days ago'}
            ]
        else:
            MOCK_DB["bookmarks"][uid] = [
                {'id': 'bm-1', 'title': 'Guide: Getting Started with AI Tutor', 'type': 'concept', 'content': '<h1>Getting Started</h1><p>Welcome to your personal AI Tutor space! You can ask questions about code, database queries, operating systems, or engineering. Your study streak increases each calendar day you engage in learning.</p>', 'created_at': 'Just now'},
                {'id': 'bm-2', 'title': 'Summary: AI Tutor Platform Guide', 'type': 'pdf', 'content': '<h1>AI Tutor Platform Guide</h1><p>The Smart AI Tutor platform includes advanced PDF Summarization, Quiz Generation, true calendar-based study streaks, and dynamic weakness detection. Click the Bookmark icon on any summary to save it here in real-time.</p>', 'created_at': 'Just now'}
            ]
    return MOCK_DB["bookmarks"][uid]'''

content = content.replace(old_get_bookmarks, new_get_bookmarks)

# Fix the toggle/add logic in save_bookmark which currently deletes based on title matching!
# It searches title EXACTLY. If you save multiple messages, they all have 'title': 'Saved AI Session'.
save_bookmark_logic_old = """        if existing_index != -1:
            # Toggle off: delete it
            bms.pop(existing_index)
            MOCK_DB['bookmarks'][uid] = bms
            return jsonify({"success": True, "action": "removed"})
        else:
            import uuid
            new_id = f"bm-{uuid.uuid4().hex[:6]}"
            bms.append({
                'id': new_id,
                'type': data.get('type', 'concept'),
                'title': data.get('title', 'Saved Item'),
                'content': data.get('content', ''),
                'created_at': 'Just now'
            })
            MOCK_DB['bookmarks'][uid] = bms
            action = "added" """

save_bookmark_logic_new = """        # Do NOT toggle off based on title alone if it's a chat session, because all chat sessions have the same title!
        # Always append!
        import uuid
        new_id = f"bm-{uuid.uuid4().hex[:6]}"
        bms.append({
            'id': new_id,
            'type': data.get('type', 'concept'),
            'title': data.get('title', 'Saved Item'),
            'content': data.get('content', ''),
            'created_at': 'Just now'
        })
        MOCK_DB['bookmarks'][uid] = bms
        action = "added" """

content = content.replace(save_bookmark_logic_old, save_bookmark_logic_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
