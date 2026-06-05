import re
import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update MOCK_DB initialization
content = content.replace(
    'MOCK_DB = {"bookmarks": {}, "activities": {}, "tasks": {}, "stats": {}, "quizzes": {}}',
    'MOCK_DB = {"bookmarks": {}, "activities": {}, "tasks": {}, "stats": {}, "quizzes": {}, "history": {}}'
)

# 2. Add get_mock_history function
history_func = """
def get_mock_history():
    uid = get_user_id()
    if "history" not in MOCK_DB:
        MOCK_DB["history"] = {}
    if uid not in MOCK_DB["history"]:
        MOCK_DB["history"][uid] = []
    return MOCK_DB["history"][uid]

def get_mock_bookmarks():"""

content = content.replace("def get_mock_bookmarks():", history_func)

# 3. Update /tutor route
tutor_route_old = """@app.route('/tutor')
@login_required
def tutor():
    user = session['user']
    sessions = []
    if supabase and user.get('id') != '1234':
        try:
            res = supabase.table('bookmarks').select('*').eq('user_id', user.get('id')).in_('type', ['session', 'chat']).order('created_at', desc=True).execute()
            sessions = res.data
        except Exception as e:
            print("Error fetching tutor sessions, falling back to mock:", e)
    else:
        # Mock fallback
        all_bms = get_mock_bookmarks()
        sessions = [b for b in all_bms if b.get('type') in ['session', 'chat']]
        
    return render_template('tutor.html', user=user, sessions=sessions)"""

tutor_route_new = """@app.route('/tutor')
@login_required
def tutor():
    user = session['user']
    history = []
    if supabase and user.get('id') != '1234':
        try:
            # For DB mode, we still read bookmarks for now, or you could create a separate history table.
            # To avoid schema changes for the user right now, we will just use mock history or DB bookmarks.
            res = supabase.table('bookmarks').select('*').eq('user_id', user.get('id')).in_('type', ['session', 'chat']).order('created_at', desc=True).execute()
            history = res.data
        except Exception as e:
            print("Error fetching tutor sessions, falling back to mock:", e)
            history = get_mock_history()
    else:
        # Mock fallback
        history = get_mock_history()
        # Sort by latest first
        history = sorted(history, key=lambda x: x.get('updated_at', ''), reverse=True)
        
    return render_template('tutor.html', user=user, history=history)"""

content = content.replace(tutor_route_old, tutor_route_new)

# 4. Add /api/history route
api_history = """
@app.route('/api/history', methods=['POST'])
@login_required
def save_history():
    data = request.json
    uid = get_user_id()
    session_id = str(data.get('session_id', ''))
    title = data.get('title', 'New Chat')
    html_content = data.get('content', '')
    
    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400
        
    hist = get_mock_history()
    
    # Check if session exists
    existing_idx = -1
    for idx, h in enumerate(hist):
        if h.get('id') == session_id:
            existing_idx = idx
            break
            
    if existing_idx != -1:
        # Update
        hist[existing_idx]['content'] = html_content
        hist[existing_idx]['updated_at'] = datetime.datetime.now().isoformat()
    else:
        # Create
        hist.append({
            'id': session_id,
            'title': title,
            'content': html_content,
            'updated_at': datetime.datetime.now().isoformat()
        })
        
    MOCK_DB['history'][uid] = hist
    save_mock_db()
    
    return jsonify({"success": True})

@app.route('/api/chat', methods=['POST'])"""

content = content.replace("@app.route('/api/chat', methods=['POST'])", api_history)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected history routes successfully.")
