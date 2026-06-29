import sys
sys.modules['google._upb._message'] = None
sys.modules['google._upb'] = None
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import markdown
import json
import tempfile
import datetime
import os

# Global in-memory storage to bypass Flask 4KB cookie limit in mock mode
# Backed by a JSON file to survive auto-reloads!
MOCK_DB_FILE = 'mock_db.json'
if os.path.exists(MOCK_DB_FILE):
    try:
        with open(MOCK_DB_FILE, 'r') as f:
            MOCK_DB = json.load(f)
    except Exception:
        MOCK_DB = {"bookmarks": {}, "activities": {}, "tasks": {}, "stats": {}, "quizzes": {}, "history": {}}
else:
    MOCK_DB = {"bookmarks": {}, "activities": {}, "tasks": {}, "stats": {}, "quizzes": {}, "history": {}}

def save_mock_db():
    try:
        with open(MOCK_DB_FILE, 'w') as f:
            json.dump(MOCK_DB, f)
    except Exception as e:
        print(f"Failed to save mock db: {e}")
from email_validator import validate_email  # type: ignore

# Helper functions for isolated per-user mock session storage
import hashlib
import time
import re

def call_gemini_with_retry(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str and "retry in" in error_str and attempt < max_retries - 1:
                wait_time = 30
                match = re.search(r"retry in ([\d\.]+)s", error_str)
                if match:
                    wait_time = float(match.group(1)) + 1
                if wait_time > 10:
                    raise e # Don't hang the UI for more than 10 seconds
                print(f"Rate limit hit. Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise e

def get_user_id():
    return session.get('user', {}).get('id', 'default_user')

def get_mock_activities():
    uid = get_user_id()
    key = f"mock_activities_{uid}"
    if key not in session:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            session[key] = [
                {'type': 'chat', 'title': 'Asked about "Deadlock Prevention"', 'description': 'AI Tutor explained the 4 conditions and prevention strategies.', 'created_at': '2 hours ago'},
                {'type': 'quiz', 'title': 'Completed "Operating Systems" Quiz', 'description': 'Scored 9/10. Great job!', 'created_at': 'Yesterday'}
            ]
        else:
            session[key] = []
    return session[key]


def get_mock_history():
    uid = get_user_id()
    if "history" not in MOCK_DB:
        MOCK_DB["history"] = {}
    if uid not in MOCK_DB["history"]:
        MOCK_DB["history"][uid] = []
    return MOCK_DB["history"][uid]

def get_mock_bookmarks():
    uid = get_user_id()
    if uid not in MOCK_DB["bookmarks"]:
        MOCK_DB["bookmarks"][uid] = []
    return MOCK_DB["bookmarks"][uid]


def get_mock_tasks():
    uid = get_user_id()
    key = f"mock_tasks_{uid}"
    if key not in session:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            session[key] = [
                {'title': 'Review OS notes', 'is_completed': True, 'priority': 'Low'}, 
                {'title': 'Take practice quiz on DBMS', 'is_completed': False, 'priority': 'High'}
            ]
        else:
            session[key] = [
                {'title': 'Welcome to AI Tutor! Review the AI Tutor guide on the Tutor page.', 'is_completed': False, 'priority': 'High'}
            ]
    return session[key]

def get_mock_quizzes():
    uid = get_user_id()
    key = f"mock_quizzes_{uid}"
    if key not in session:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            # student has an existing low-score quiz in Database Normalization to trigger weakness
            session[key] = [
                {'topic': 'Database Normalization', 'score': 1, 'num_questions': 3, 'percentage': 33, 'created_at': 'Yesterday'}
            ]
        else:
            session[key] = []
    return session[key]

def refresh_mock_streak(uid):
    stats_key = f"mock_stats_{uid}"
    if stats_key not in session:
        email = session.get('user', {}).get('email', '')
        if email == 'student@example.com' or email == '':
            yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            session[stats_key] = {'study_streak': 12, 'topics_mastered': 48, 'avg_quiz_score': 86, 'last_active_date': yesterday}
        else:
            session[stats_key] = {'study_streak': 0, 'topics_mastered': 0, 'avg_quiz_score': 0, 'last_active_date': None}
            
    m_stats = session[stats_key]
    last_active = m_stats.get('last_active_date')
    if last_active:
        try:
            last_date = datetime.datetime.strptime(last_active, '%Y-%m-%d').date()
            today_date = datetime.date.today()
            delta = (today_date - last_date).days
            if delta > 1:
                # User missed a day, reset streak to 0
                m_stats['study_streak'] = 0
                session[stats_key] = m_stats
                session.modified = True
        except Exception as e:
            print(f"Error parsing streak date in refresh: {e}")

def update_mock_streak(uid):
    stats_key = f"mock_stats_{uid}"
    refresh_mock_streak(uid)
    
    m_stats = session[stats_key]
    today = datetime.date.today().strftime('%Y-%m-%d')
    last_active = m_stats.get('last_active_date')
    streak = m_stats.get('study_streak', 0)
    
    if not last_active:
        streak = 1
    else:
        try:
            last_date = datetime.datetime.strptime(last_active, '%Y-%m-%d').date()
            today_date = datetime.date.today()
            delta = (today_date - last_date).days
            if delta == 1:
                streak += 1
            elif delta > 1 or streak == 0:
                streak = 1
            # If delta == 0, keep same
        except Exception as e:
            print(f"Error parsing streak date in update: {e}")
            streak = 1
            
    m_stats['study_streak'] = streak
    m_stats['last_active_date'] = today
    session[stats_key] = m_stats
    session.modified = True

# Load environment variables
load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-123")
app.permanent_session_lifetime = datetime.timedelta(days=30)

# Initialize Supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
if supabase_url and supabase_key:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as db_err:
        supabase = None
        print(f"Warning: Failed to initialize Supabase client ({db_err}). Falling back to Mock Mode.")
else:
    supabase = None
    print("Warning: Supabase credentials not found. DB features will not work.")

# Initialize Gemini
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    # Using a modern flash model for faster responses
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None
    print("Warning: Gemini API Key not found. AI features will not work.")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            if supabase:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                session['user'] = {
                    'id': res.user.id,
                    'email': res.user.email,
                    'name': res.user.user_metadata.get('name', 'Student')
                }
            else:
                # Mock registry to load actual signed up name
                if 'mock_users' in session and email in session['mock_users']:
                    if session['mock_users'][email]['password'] != password:
                        raise Exception("Invalid credentials.")
                    name = session['mock_users'][email]['name']
                else:
                    raise Exception("Account does not exist. Please sign up first.")
                
                user_id = hashlib.md5(email.encode('utf-8')).hexdigest()
                session['user'] = {
                    'id': user_id,
                    'email': email,
                    'name': name
                }
            session.permanent = True
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('auth.html', is_login=True, error=str(e))
    return render_template('auth.html', is_login=True)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            if supabase:
                supabase.auth.reset_password_email(email)
            return render_template('auth.html', is_login=True, success="If an account with that email exists, a password reset link has been sent.")
        except Exception as e:
            return render_template('auth.html', is_forgot=True, error=str(e))
    return render_template('auth.html', is_forgot=True)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        try:
            # Validate email
            v = validate_email(email, check_deliverability=True)
            email = v.normalized

            if supabase:
                res = supabase.auth.sign_up({
                    "email": email, 
                    "password": password,
                    "options": {"data": {"name": name}}
                })
                # Create profile and stats records
                if res.user:
                    try:
                        supabase.table('profiles').insert({'id': res.user.id, 'name': name, 'email': email}).execute()
                        supabase.table('user_stats').insert({'user_id': res.user.id}).execute()
                    except Exception as db_e:
                        print(f"Warning: Failed to create initial DB records for user (tables might be missing): {db_e}")
            else:
                # Store registered users locally in session registry
                if 'mock_users' not in session:
                    session['mock_users'] = {}
                session['mock_users'][email] = {'name': name, 'password': password}
                session.modified = True
            
            # After creating account, do not log them in directly. Redirect to login with success message.
            return render_template('auth.html', is_login=True, success="Account created successfully! Please sign in with your credentials.")
        except Exception as e:
            # Fallback for testing: if Supabase throws an auth error, we can optionally bypass it,
            # but it's better to show the error. We will just pass it to the template.
            return render_template('auth.html', is_login=False, error=str(e))
    return render_template('auth.html', is_login=False)

@app.route('/logout')
def logout():
    if supabase:
        supabase.auth.sign_out()
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = session['user']
    stats, activities, bookmarks, tasks = None, [], [], []
    
    if supabase and user.get('id') != '1234':
        try:
            # Fetch user stats
            stats_res = supabase.table('user_stats').select('*').eq('user_id', user['id']).execute()
            stats = stats_res.data[0] if stats_res.data else {'study_streak': 0, 'topics_mastered': 0, 'avg_quiz_score': 0}
            
            # Fetch recent activity
            act_res = supabase.table('activities').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(5).execute()
            activities = act_res.data
            
            # Fetch bookmarks
            bm_res = supabase.table('bookmarks').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(5).execute()
            bookmarks = bm_res.data
            
            # Fetch tasks
            tasks_res = supabase.table('study_tasks').select('*').eq('user_id', user['id']).order('created_at', desc=True).execute()
            tasks = tasks_res.data
        except Exception as e:
            print("Error fetching dashboard data, falling back to mock:", e)
            uid = get_user_id()
            refresh_mock_streak(uid)
            stats = session[f"mock_stats_{uid}"]
            activities = get_mock_activities()[::-1]  # Get all activities, let frontend decide limit/modal
            bookmarks = get_mock_bookmarks()[::-1][:10]
            tasks = get_mock_tasks()
            
    else:
        # Mock data if no DB connection
        uid = get_user_id()
        refresh_mock_streak(uid)
        stats = session[f"mock_stats_{uid}"]
        activities = get_mock_activities()[::-1]  # Get all activities, let frontend decide limit/modal
        bookmarks = get_mock_bookmarks()[::-1][:10]
        tasks = get_mock_tasks()

    # Calculate dynamic weaknesses
    uid = get_user_id()
    weakness = None
    all_quizzes = []
    
    if supabase and user.get('id') != '1234':
        try:
            # Query recent quiz activities from remote DB
            act_res = supabase.table('activities').select('*').eq('user_id', user['id']).eq('type', 'quiz').execute()
            for act in act_res.data:
                desc = act.get('description', '')
                title = act.get('title', '')
                topic = title.replace('Completed Quiz on "', '').replace('"', '')
                try:
                    if '(' in desc and '%' in desc:
                        pct_str = desc.split('(')[-1].split('%')[0]
                        pct = int(pct_str)
                        all_quizzes.append({'topic': topic, 'percentage': pct})
                except Exception as parse_err:
                    print(f"Error parsing quiz percentage: {parse_err}")
        except Exception as db_err:
            print("Error fetching quizzes for weakness analysis:", db_err)
            
    if not all_quizzes:
        all_quizzes = get_mock_quizzes()
        
    if all_quizzes:
        topic_scores = {}
        for q in all_quizzes:
            t = q.get('topic', 'AI Quiz')
            pct = q.get('percentage', q.get('score', 0)) # fallback to score directly if percentage is missing
            if t not in topic_scores:
                topic_scores[t] = []
            topic_scores[t].append(pct)
            
        topic_avgs = {}
        for t, scores in topic_scores.items():
            topic_avgs[t] = int(sum(scores) / len(scores))
            
        if topic_avgs:
            lowest_topic = min(topic_avgs, key=topic_avgs.get)
            lowest_score = topic_avgs[lowest_topic]
            
            # If the lowest average score is less than 70%, suggest it as a weakness!
            if lowest_score < 70:
                weakness = {'topic': lowest_topic, 'score': lowest_score}

    return render_template('dashboard.html', user=user, stats=stats, activities=activities, bookmarks=bookmarks, tasks=tasks, weakness=weakness)

@app.route('/tutor')
@login_required
def tutor():
    user = session['user']
    
    # Always fetch auto-saved history from the persistent mock DB
    history = get_mock_history()
    # Sort by latest first
    history = sorted(history, key=lambda x: x.get('updated_at', ''), reverse=True)
        
    return render_template('tutor.html', user=user, history=history)

@app.route('/pdf_summarizer')
@login_required
def pdf_summarizer():
    user = session['user']
    summaries = []
    if supabase and user.get('id') != '1234':
        try:
            res = supabase.table('bookmarks').select('*').eq('user_id', user['id']).eq('type', 'pdf').order('created_at', desc=True).execute()
            summaries = res.data
        except Exception as e:
            print("Error fetching pdf summaries:", e)
            summaries = [b for b in get_mock_bookmarks() if b.get('type') == 'pdf']
    else:
        summaries = [b for b in get_mock_bookmarks() if b.get('type') == 'pdf']
        
    # Sort with newest first
    summaries = summaries[::-1]
    return render_template('pdf_summarizer.html', user=user, summaries=summaries)

@app.route('/bookmarks')
@login_required
def bookmarks():
    user = session['user']
    bookmarks_list = []
    if supabase and user.get('id') != '1234':
        try:
            bm_res = supabase.table('bookmarks').select('*').eq('user_id', user['id']).order('created_at', desc=True).execute()
            bookmarks_list = bm_res.data
        except Exception as e:
            print("Error fetching bookmarks, falling back to mock:", e)
            bookmarks_list = get_mock_bookmarks()
    else:
        bookmarks_list = get_mock_bookmarks()
    return render_template('bookmarks.html', user=user, bookmarks=bookmarks_list)

@app.route('/quiz')
@login_required
def quiz():
    return render_template('quiz.html', user=session['user'])

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html', user=session['user'])

def log_activity(user_id, act_type, title, description):
    success = False
    if supabase and user_id != '1234':
        try:
            supabase.table('activities').insert({
                'user_id': user_id,
                'type': act_type,
                'title': title,
                'description': description
            }).execute()
            success = True
        except Exception as e:
            print(f"Error logging activity to DB, falling back to mock: {e}")
            
    if not success:
        uid = get_user_id()
        acts = get_mock_activities()
        acts.append({
            'type': act_type,
            'title': title,
            'description': description,
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        MOCK_DB['activities'][uid] = acts
        save_mock_db()

@app.route('/api/bookmarks', methods=['POST'])
@login_required
def save_bookmark():
    data = request.json
    success = False
    action = "added"
    
    if supabase and session['user'].get('id') != '1234':
        try:
            # Check if title already exists to unbookmark (toggle)
            existing = supabase.table('bookmarks').select('*').eq('user_id', session['user'].get('id')).eq('title', data.get('title')).execute()
            if existing.data:
                supabase.table('bookmarks').delete().eq('id', existing.data[0]['id']).execute()
                return jsonify({"success": True, "action": "removed"})
            else:
                supabase.table('bookmarks').insert({
                    'user_id': session['user'].get('id', '1234'),
                    'type': data.get('type', 'concept'),
                    'title': data.get('title', 'Saved Item'),
                    'content': data.get('content', '')
                }).execute()
                success = True
                action = "added"
        except Exception as e:
            print(f"Error saving bookmark to DB, falling back to mock: {e}")
            
    if not success:
        # Mock fallback
        uid = get_user_id()
        bms = get_mock_bookmarks()
        
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
        save_mock_db()
        action = "added"
            
    return jsonify({"success": True, "action": action})

@app.route('/api/bookmarks/<bookmark_id>', methods=['DELETE'])
@login_required
def delete_bookmark(bookmark_id):
    success = False
    if supabase and session['user'].get('id') != '1234':
        try:
            supabase.table('bookmarks').delete().eq('id', bookmark_id).eq('user_id', session['user'].get('id')).execute()
            success = True
        except Exception as e:
            print(f"Error deleting bookmark from DB, falling back to mock: {e}")
            
    if not success:
        uid = get_user_id()
        bms = get_mock_bookmarks()
        MOCK_DB['bookmarks'][uid] = [b for b in bms if b.get('id') != bookmark_id]
        save_mock_db()
        
    return jsonify({"success": True})

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    data = request.json
    success = False
    
    # Check if this is a toggle request
    action = data.get('action', 'add')
    
    if supabase and session['user'].get('id') != '1234':
        try:
            if action == 'add':
                supabase.table('study_tasks').insert({
                    'user_id': session['user'].get('id', '1234'),
                    'title': data.get('title', 'New Task'),
                    'priority': data.get('priority', 'Med'),
                    'is_completed': False
                }).execute()
            elif action == 'toggle':
                task_id = data.get('id')
                title = data.get('title')
                if task_id:
                    tasks = supabase.table('study_tasks').select('is_completed').eq('id', task_id).execute()
                    if tasks.data:
                        supabase.table('study_tasks').update({'is_completed': not tasks.data[0]['is_completed']}).eq('id', task_id).execute()
                elif title:
                    tasks = supabase.table('study_tasks').select('id, is_completed').eq('title', title).eq('user_id', session['user'].get('id')).execute()
                    if tasks.data:
                        supabase.table('study_tasks').update({'is_completed': not tasks.data[0]['is_completed']}).eq('id', tasks.data[0]['id']).execute()
            success = True
        except Exception as e:
            print(f"Error saving task to DB, falling back to mock: {e}")
            
    if not success:
        uid = get_user_id()
        ts = get_mock_tasks()
        if action == 'add':
            ts.append({
                'title': data.get('title', 'New Task'),
                'priority': data.get('priority', 'Med'),
                'is_completed': False
            })
        elif action == 'toggle':
            title = data.get('title')
            for t in ts:
                if t['title'] == title:
                    t['is_completed'] = not t['is_completed']
                    break
        session[f"mock_tasks_{uid}"] = ts
        session.modified = True
    
    return jsonify({"success": True})

@app.route('/api/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    data = request.json
    score = data.get('score', 0)
    topic = data.get('topic', 'AI Quiz')
    num_questions = data.get('num_questions', 3)
    percentage = int((score / num_questions) * 100) if num_questions > 0 else 0
    
    user_id = session['user'].get('id', '1234')
    
    # Log the activity
    log_activity(user_id, 'quiz', f'Completed Quiz on "{topic}"', f'Scored {score}/{num_questions} ({percentage}%).')
    
    # Update Stats
    success = False
    if supabase and user_id != '1234':
        try:
            # Fetch current stats
            stats_res = supabase.table('user_stats').select('*').eq('user_id', user_id).execute()
            if stats_res.data:
                stats = stats_res.data[0]
                new_streak = stats.get('study_streak', 0) + 1
                new_topics = stats.get('topics_mastered', 0)
                if percentage >= 70:
                    new_topics += 1
                
                avg_score = float(stats.get('avg_quiz_score', 0.00))
                new_avg = (avg_score + percentage) / 2 if avg_score > 0 else percentage
                
                supabase.table('user_stats').update({
                    'study_streak': new_streak,
                    'topics_mastered': new_topics,
                    'avg_quiz_score': round(new_avg, 2)
                }).eq('user_id', user_id).execute()
                success = True
        except Exception as e:
            print(f"Error updating stats in DB: {e}")
            
    # Always append the quiz result to mock quizzes list for real-time tracking
    uid = get_user_id()
    quizzes = get_mock_quizzes()
    quizzes.append({
        'topic': topic,
        'score': score,
        'num_questions': num_questions,
        'percentage': percentage,
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    session[f"mock_quizzes_{uid}"] = quizzes
    session.modified = True

    if not success:
        uid = get_user_id()
        update_mock_streak(uid)
        
        stats_key = f"mock_stats_{uid}"
        m_stats = session[stats_key]
        if percentage >= 70:
            m_stats['topics_mastered'] += 1
        
        old_avg = m_stats['avg_quiz_score']
        m_stats['avg_quiz_score'] = round((old_avg + percentage) / 2, 1)
        session[stats_key] = m_stats
        session.modified = True
        
    return jsonify({"success": True})

# API Endpoints

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

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    if not model:
        return jsonify({"error": "AI not configured"}), 500
        
    data = request.json
    message = data.get('message', '')
    history_data = data.get('history', [])
    
    # Prompt to determine if it's a topic or question
    sys_prompt = """
    You are an expert AI Tutor. 
    First, determine if the user input is a short topic (e.g., "Deadlock", "Photosynthesis") or a specific question/doubt (e.g., "Explain deadlock prevention", "Why is the sky blue?").
    If it's a short topic, provide a full overview including definition, key concepts, examples, and resources. Structure it well using Markdown.
    If it's a specific question, provide a precise, focused answer. Explain step-by-step.
    
    IMPORTANT RULES:
    1. NEVER use image placeholders or markdown images (like ![image](url)). You must explain everything textually.
    2. Format all mathematical formulas using standard LaTeX notation so they can be rendered properly. Enclose inline math in \\( and \\) and block math in \\[ and \\]. Do NOT use plain text symbols for complex equations.
    """
    
    try:
        # Convert frontend history to Gemini format if necessary, though we can just build the prompt 
        # using the history manually to keep the sys_prompt context intact at the start.
        # However, model.start_chat() is the cleaner way if we want true conversational memory.
        
        # We will inject the sys_prompt on the first message or keep it as an instruction.
        # Actually, we can just use start_chat(history=...) if we convert it.
        chat_history = []
        for h in history_data:
            role = 'model' if h.get('sender') == 'ai' else 'user'
            chat_history.append({
                "role": role,
                "parts": [h.get('text')]
            })
            
        chat = model.start_chat(history=chat_history)
        
        # Prepend system prompt to the actual message so the model always remembers its persona
        full_message = f"{sys_prompt}\n\nUser Input: {message}"
        
        response = call_gemini_with_retry(chat.send_message, full_message)
        
        # Log activity
        log_activity(session['user'].get('id', '1234'), 'chat', f'Asked: "{message[:30]}..."', 'Interacted with AI Tutor.')
        
        # Update calendar streak
        uid = get_user_id()
        update_mock_streak(uid)
        
        # We need to render the markdown but keep the latex tags intact for MathJax.
        # Python-markdown might escape some symbols. To prevent this, we can just return the raw text
        # and let marked.js + MathJax on the frontend handle it, OR we just use a basic markdown render.
        # To avoid python-markdown destroying MathJax formulas, it's safer to return the raw text 
        # and parse markdown on the frontend, BUT we already use python-markdown. Let's stick to it 
        # but MathJax will usually still parse \( x \) inside HTML.
        html_response = markdown.markdown(response.text, extensions=['fenced_code', 'tables'])
        return jsonify({"response": html_response, "raw_text": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_quiz', methods=['POST'])
@login_required
def api_generate_quiz():
    if not model:
        return jsonify({"error": "AI not configured"}), 500
        
    data = request.json
    topic = data.get('topic', '')
    num_questions = data.get('num_questions', 5)
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
        
    sys_prompt = f"""
    You are an expert AI Quiz Generator. Generate a multiple-choice quiz about "{topic}" with {num_questions} questions.
    Return ONLY a valid JSON array of objects. Do not wrap in markdown tags like ```json.
    Each object must have the following format:
    {{
        "question": "The question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0, // index of the correct option (0-3)
        "explanation": "Explanation of why this answer is correct."
    }}
    """
    
    try:
        response = call_gemini_with_retry(model.generate_content, sys_prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        quiz_data = json.loads(response_text)
        
        # Log activity
        log_activity(session['user'].get('id', '1234'), 'quiz', f'Generated Quiz on "{topic}"', f'{num_questions} questions generated.')
        
        return jsonify({"quiz": quiz_data})
    except Exception as e:
        return jsonify({"error": str(e), "raw_response": response.text if 'response' in locals() else ""}), 500

@app.route('/api/summarize_pdf', methods=['POST'])
@login_required
def api_summarize_pdf():
    if not model:
        return jsonify({"error": "AI not configured"}), 500
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.endswith('.pdf'):
        try:
            # Save file temporarily
            fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            file.save(temp_pdf_path)
            
            # Upload to Gemini File API
            # Gemini handles OCR for scanned PDFs natively
            uploaded_file = genai.upload_file(path=temp_pdf_path, display_name=file.filename)
            
            # Wait for Gemini to process the PDF
            import time
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini failed to process the uploaded PDF.")
            
            # Generate content using the uploaded file
            sys_prompt = "You are an expert summarizer. Please provide a comprehensive summary of the provided document. Structure the summary with a main overview, key points in bullet points, and any notable conclusions. Format the response in Markdown."
            
            response = call_gemini_with_retry(model.generate_content, [sys_prompt, uploaded_file])
            
            # Clean up the file from Gemini
            genai.delete_file(uploaded_file.name)
            
            # Clean up local temp file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                
            # Log activity
            log_activity(session['user'].get('id', '1234'), 'pdf', f'Summarized "{file.filename}"', 'Generated an AI summary.')
            
            # Update study streak
            uid = get_user_id()
            update_mock_streak(uid)
                
            html_response = markdown.markdown(response.text)
            return jsonify({"summary": html_response, "raw_markdown": response.text})
            
        except Exception as e:
            # Attempt cleanup on error
            if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file format. Please upload a PDF."}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
