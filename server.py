from flask import Flask, request, jsonify, session, send_from_directory, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
from datetime import datetime, timedelta
import secrets

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
CORS(app, supports_credentials=True)

DB_PATH = 'society_system.db'
USER_DATA_DIR = 'user_data'

def init_db():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        phone TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS page_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page TEXT NOT NULL,
        visitor_id TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        cover_image TEXT,
        author_id INTEGER NOT NULL,
        publish_date TEXT NOT NULL,
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'published',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(id)
    )''')
    
    # 创建默认管理员
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, email, name, role) VALUES (?, ?, ?, ?, ?)",
                  ('admin', generate_password_hash('admin123'), 'admin@system.com', '系统管理员', 'admin'))
    
    conn.commit()
    conn.close()

def create_user_folder(user_id):
    user_dir = os.path.join(USER_DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(os.path.join(user_dir, 'clubs'), exist_ok=True)
    os.makedirs(os.path.join(user_dir, 'activities'), exist_ok=True)
    with open(os.path.join(user_dir, 'profile.json'), 'w', encoding='utf-8') as f:
        json.dump({'created_at': datetime.now().isoformat()}, f)

def check_session():
    token = request.headers.get('Authorization')
    if not token:
        return None, {'error': 'SESSION_TIMEOUT', 'code': 401, 'message': '会话超时，请重新登录'}
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT s.user_id, u.username, u.name, u.role, u.email 
                 FROM sessions s JOIN users u ON s.user_id = u.id 
                 WHERE s.token = ? AND s.expires_at > ?''', 
              (token, datetime.now()))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return None, {'error': 'SESSION_EXPIRED', 'code': 401, 'message': '会话已过期，请重新登录'}
    
    return {'id': result[0], 'username': result[1], 'name': result[2], 'role': result[3], 'email': result[4]}, None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    name = data.get('name', username)
    role = 'student'  # 默认只能注册学生账户
    phone = data.get('phone', '')
    
    if not all([username, password, email]):
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password, email, name, role, phone) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, generate_password_hash(password), email, name, role, phone))
        user_id = c.lastrowid
        conn.commit()
        create_user_folder(user_id)
        return jsonify({'success': True, 'message': '注册成功'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': '用户名或邮箱已存在'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password, name, role, email, status FROM users WHERE username = ? OR email = ?", (username, username))
    user = c.fetchone()
    
    if not user or not check_password_hash(user[2], password):
        conn.close()
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    if user[6] == 'inactive':
        conn.close()
        return jsonify({'success': False, 'message': '账户已被禁用'}), 403
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=2)
    c.execute("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
              (user[0], token, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user[0],
            'username': user[1],
            'name': user[3],
            'role': user[4],
            'email': user[5],
            'status': user[6],
            'needsProfile': user[6] == 'pending'  # 首次登录标记
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return jsonify({'success': True})

@app.route('/api/check-session', methods=['GET'])
def check_session_route():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    return jsonify({'success': True, 'user': user})

@app.route('/api/users', methods=['GET'])
def get_users():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, email, name, role, phone, status, created_at FROM users")
    users = [{'id': r[0], 'username': r[1], 'email': r[2], 'name': r[3], 
              'role': r[4], 'phone': r[5], 'status': r[6], 'created_at': r[7]} 
             for r in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'users': users})

@app.route('/api/user/<int:user_id>', methods=['PUT', 'DELETE'])
def manage_user(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        c.execute('''UPDATE users SET username=?, email=?, name=?, role=?, phone=?, status=? 
                     WHERE id=?''',
                  (data['username'], data['email'], data['name'], data['role'], 
                   data.get('phone', ''), data.get('status', 'active'), user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        c.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/user/create-teacher', methods=['POST'])
def create_teacher():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    name = data.get('name', username)
    password = secrets.token_urlsafe(8)  # 生成随机密码
    
    if not all([username, email]):
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password, email, name, role, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, generate_password_hash(password), email, name, 'teacher', 'pending'))
        user_id = c.lastrowid
        conn.commit()
        create_user_folder(user_id)
        return jsonify({'success': True, 'message': '教师账户创建成功', 'password': password, 'user_id': user_id})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': '用户名或邮箱已存在'}), 400
    finally:
        conn.close()

@app.route('/api/user/<int:user_id>/profile', methods=['GET', 'POST'])
def user_profile(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['id'] != user_id and user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    user_dir = os.path.join(USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir):
        create_user_folder(user_id)
    
    profile_file = os.path.join(user_dir, 'profile.json')
    
    if request.method == 'GET':
        if os.path.exists(profile_file):
            with open(profile_file, 'r', encoding='utf-8') as f:
                return jsonify({'success': True, 'profile': json.load(f)})
        return jsonify({'success': True, 'profile': {}})
    
    elif request.method == 'POST':
        data = request.json
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})

@app.route('/api/user/<int:user_id>/data', methods=['GET', 'POST'])
def user_data(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['id'] != user_id and user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    user_dir = os.path.join(USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir):
        create_user_folder(user_id)
    
    data_type = request.args.get('type', 'profile')
    file_path = os.path.join(user_dir, f'{data_type}.json')
    
    if request.method == 'GET':
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify({'success': True, 'data': json.load(f)})
        return jsonify({'success': True, 'data': {}})
    
    elif request.method == 'POST':
        data = request.json
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})

@app.route('/api/user/<int:user_id>/clubs', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_clubs(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['id'] != user_id and user['role'] not in ['admin', 'teacher']:
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    clubs_dir = os.path.join(USER_DATA_DIR, str(user_id), 'clubs')
    os.makedirs(clubs_dir, exist_ok=True)
    
    if request.method == 'GET':
        clubs = []
        for filename in os.listdir(clubs_dir):
            if filename.endswith('.json'):
                with open(os.path.join(clubs_dir, filename), 'r', encoding='utf-8') as f:
                    club = json.load(f)
                    club['id'] = filename[:-5]
                    clubs.append(club)
        return jsonify({'success': True, 'clubs': clubs})
    
    elif request.method == 'POST':
        data = request.json
        club_id = secrets.token_urlsafe(8)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        with open(os.path.join(clubs_dir, f'{club_id}.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'id': club_id})
    
    elif request.method == 'PUT':
        club_id = request.args.get('id')
        if not club_id:
            return jsonify({'error': 'MISSING_ID', 'code': 400, 'message': '缺少社团ID'}), 400
        data = request.json
        data['updated_at'] = datetime.now().isoformat()
        with open(os.path.join(clubs_dir, f'{club_id}.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        club_id = request.args.get('id')
        if not club_id:
            return jsonify({'error': 'MISSING_ID', 'code': 400, 'message': '缺少社团ID'}), 400
        file_path = os.path.join(clubs_dir, f'{club_id}.json')
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': True})

@app.route('/api/user/<int:user_id>/activities', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_activities(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['id'] != user_id and user['role'] not in ['admin', 'teacher']:
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    activities_dir = os.path.join(USER_DATA_DIR, str(user_id), 'activities')
    os.makedirs(activities_dir, exist_ok=True)
    
    if request.method == 'GET':
        activities = []
        for filename in os.listdir(activities_dir):
            if filename.endswith('.json'):
                with open(os.path.join(activities_dir, filename), 'r', encoding='utf-8') as f:
                    activity = json.load(f)
                    activity['id'] = filename[:-5]
                    activities.append(activity)
        return jsonify({'success': True, 'activities': activities})
    
    elif request.method == 'POST':
        data = request.json
        activity_id = secrets.token_urlsafe(8)
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        with open(os.path.join(activities_dir, f'{activity_id}.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'id': activity_id})
    
    elif request.method == 'PUT':
        activity_id = request.args.get('id')
        if not activity_id:
            return jsonify({'error': 'MISSING_ID', 'code': 400, 'message': '缺少活动ID'}), 400
        data = request.json
        data['updated_at'] = datetime.now().isoformat()
        with open(os.path.join(activities_dir, f'{activity_id}.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        activity_id = request.args.get('id')
        if not activity_id:
            return jsonify({'error': 'MISSING_ID', 'code': 400, 'message': '缺少活动ID'}), 400
        file_path = os.path.join(activities_dir, f'{activity_id}.json')
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views WHERE page='/'")
    total_views = c.fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'views': total_views})

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 用户统计
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE status='active'")
    active_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    student_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    teacher_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    admin_count = c.fetchone()[0]
    
    # 访问统计
    c.execute("SELECT COUNT(*) FROM page_views")
    total_visits = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views")
    unique_visitors = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM page_views WHERE DATE(visited_at) = DATE('now')")
    today_visits = c.fetchone()[0]
    
    # 会话统计
    c.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')")
    active_sessions = c.fetchone()[0]
    
    # 新闻统计
    c.execute("SELECT COUNT(*) FROM news")
    news_count = c.fetchone()[0]
    
    conn.close()
    
    # 社团统计
    clubs_file = os.path.join(USER_DATA_DIR, 'clubs.json')
    club_count = 0
    total_members = 0
    if os.path.exists(clubs_file):
        with open(clubs_file, 'r', encoding='utf-8') as f:
            clubs = json.load(f)
            club_count = len(clubs)
            total_members = sum(c.get('memberCount', 0) for c in clubs)
    
    # 活动统计
    activity_count = 0
    for user_dir in os.listdir(USER_DATA_DIR):
        if user_dir.isdigit():
            activities_dir = os.path.join(USER_DATA_DIR, user_dir, 'activities')
            if os.path.exists(activities_dir):
                activity_count += len([f for f in os.listdir(activities_dir) if f.endswith('.json')])
    
    # 数据库大小
    db_size = os.path.getsize(DB_PATH) / 1024 / 1024  # MB
    
    return jsonify({
        'success': True,
        'stats': {
            'users': {
                'total': user_count,
                'active': active_users,
                'inactive': user_count - active_users,
                'student': student_count,
                'teacher': teacher_count,
                'admin': admin_count
            },
            'visits': {
                'total': total_visits,
                'unique': unique_visitors,
                'today': today_visits
            },
            'sessions': {
                'active': active_sessions
            },
            'news': {
                'total': news_count
            },
            'clubs': {
                'total': club_count,
                'totalMembers': total_members
            },
            'activities': {
                'total': activity_count
            },
            'system': {
                'db_size': round(db_size, 2)
            }
        }
    })

def track_visit(page):
    visitor_id = request.cookies.get('visitor_id')
    if not visitor_id:
        visitor_id = secrets.token_urlsafe(16)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO page_views (page, visitor_id, ip_address, user_agent) VALUES (?, ?, ?, ?)",
              (page, visitor_id, request.remote_addr, request.headers.get('User-Agent', '')))
    conn.commit()
    conn.close()
    return visitor_id

# 前端路由
@app.route('/')
def index():
    visitor_id = track_visit('/')
    response = send_from_directory('.', 'index.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.set_cookie('visitor_id', visitor_id, max_age=365*24*60*60, httponly=True, samesite='Lax')
    return response

@app.route('/login')
def login_page():
    response = send_from_directory('page/log_system', 'login.main.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/register')
def register_page():
    response = send_from_directory('page/log_system', 'register.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/home')
def home_page():
    response = send_from_directory('.', 'index.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/page/<path:filename>')
def serve_page(filename):
    response = send_from_directory('page', filename)
    if filename.endswith('.html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)

@app.route('/user_data/<path:filename>')
def serve_user_data(filename):
    return send_from_directory('user_data', filename)

@app.route('/news/<path:filename>')
def serve_news(filename):
    if filename.endswith('.html') and filename != 'detail.html':
        response = send_from_directory('news', 'detail.html')
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    response = send_from_directory('news', filename)
    if filename.endswith('.html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/news', methods=['GET', 'POST'])
def news_api():
    if request.method == 'GET':
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT n.id, n.title, n.content, n.cover_image, n.author_id, u.name, 
                     n.publish_date, n.views, n.status, n.created_at, n.updated_at
                     FROM news n JOIN users u ON n.author_id = u.id 
                     WHERE n.status = 'published' ORDER BY n.publish_date DESC''')
        news_list = [{'id': r[0], 'title': r[1], 'content': r[2], 'cover_image': r[3],
                      'author_id': r[4], 'author_name': r[5], 'publish_date': r[6],
                      'views': r[7], 'status': r[8], 'created_at': r[9], 'updated_at': r[10]}
                     for r in c.fetchall()]
        conn.close()
        return jsonify({'success': True, 'news': news_list})
    
    elif request.method == 'POST':
        user, error = check_session()
        if error:
            return jsonify(error), error['code']
        if user['role'] not in ['admin', 'teacher']:
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        data = request.json
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO news (title, content, cover_image, author_id, publish_date, status)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (data['title'], data['content'], data.get('cover_image', ''),
                   user['id'], data['publish_date'], data.get('status', 'published')))
        news_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': news_id})

@app.route('/api/news/<int:news_id>', methods=['GET', 'PUT', 'DELETE'])
def news_detail(news_id):
    if request.method == 'GET':
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE news SET views = views + 1 WHERE id = ?', (news_id,))
        c.execute('''SELECT n.id, n.title, n.content, n.cover_image, n.author_id, u.name,
                     n.publish_date, n.views, n.status FROM news n JOIN users u ON n.author_id = u.id
                     WHERE n.id = ?''', (news_id,))
        row = c.fetchone()
        conn.commit()
        conn.close()
        if not row:
            return jsonify({'error': 'NOT_FOUND', 'code': 404}), 404
        return jsonify({'success': True, 'news': {
            'id': row[0], 'title': row[1], 'content': row[2], 'cover_image': row[3],
            'author_id': row[4], 'author_name': row[5], 'publish_date': row[6],
            'views': row[7], 'status': row[8]
        }})
    
    elif request.method == 'PUT':
        user, error = check_session()
        if error:
            return jsonify(error), error['code']
        if user['role'] != 'admin':
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        data = request.json
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''UPDATE news SET title=?, content=?, cover_image=?, publish_date=?, 
                     status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''',
                  (data['title'], data['content'], data.get('cover_image', ''),
                   data['publish_date'], data.get('status', 'published'), news_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        user, error = check_session()
        if error:
            return jsonify(error), error['code']
        if user['role'] != 'admin':
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM news WHERE id = ?', (news_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/banners', methods=['GET', 'POST'])
def banners_api():
    if request.method == 'GET':
        config_file = os.path.join('user_data', 'banners.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({'success': True, 'banners': data.get('banners', [])})
        return jsonify({'success': True, 'banners': []})
    
    elif request.method == 'POST':
        user, error = check_session()
        if error:
            return jsonify(error), error['code']
        if user['role'] != 'admin':
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        data = request.json
        config_file = os.path.join('user_data', 'banners.json')
        os.makedirs('user_data', exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'banners': data.get('banners', [])}, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})

from werkzeug.utils import secure_filename
import uuid

@app.route('/api/clubs', methods=['GET', 'POST'])
def clubs_api():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    clubs_file = os.path.join(USER_DATA_DIR, 'clubs.json')
    
    if request.method == 'GET':
        if os.path.exists(clubs_file):
            with open(clubs_file, 'r', encoding='utf-8') as f:
                clubs = json.load(f)
                return jsonify({'success': True, 'clubs': clubs})
        return jsonify({'success': True, 'clubs': []})
    
    elif request.method == 'POST':
        if user['role'] not in ['admin', 'teacher']:
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        data = request.json
        data['id'] = secrets.token_urlsafe(8)
        data['created_at'] = datetime.now().isoformat()
        data['memberCount'] = 0
        
        clubs = []
        if os.path.exists(clubs_file):
            with open(clubs_file, 'r', encoding='utf-8') as f:
                clubs = json.load(f)
        
        clubs.append(data)
        
        with open(clubs_file, 'w', encoding='utf-8') as f:
            json.dump(clubs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'id': data['id']})

@app.route('/api/clubs/<club_id>', methods=['GET', 'PUT', 'DELETE'])
def club_detail(club_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    clubs_file = os.path.join(USER_DATA_DIR, 'clubs.json')
    
    if not os.path.exists(clubs_file):
        return jsonify({'error': 'NOT_FOUND', 'code': 404}), 404
    
    with open(clubs_file, 'r', encoding='utf-8') as f:
        clubs = json.load(f)
    
    club = next((c for c in clubs if c['id'] == club_id), None)
    
    if request.method == 'GET':
        if not club:
            return jsonify({'error': 'NOT_FOUND', 'code': 404}), 404
        return jsonify({'success': True, 'club': club})
    
    elif request.method == 'PUT':
        if user['role'] not in ['admin', 'teacher']:
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        if not club:
            return jsonify({'error': 'NOT_FOUND', 'code': 404}), 404
        
        data = request.json
        club.update(data)
        club['updated_at'] = datetime.now().isoformat()
        
        with open(clubs_file, 'w', encoding='utf-8') as f:
            json.dump(clubs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        if user['role'] != 'admin':
            return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
        
        clubs = [c for c in clubs if c['id'] != club_id]
        
        with open(clubs_file, 'w', encoding='utf-8') as f:
            json.dump(clubs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})

@app.route('/api/clubs/join', methods=['POST'])
def join_club():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    data = request.json
    # 保存加入申请到用户数据
    user_dir = os.path.join(USER_DATA_DIR, str(user['id']))
    requests_file = os.path.join(user_dir, 'club_requests.json')
    
    requests = []
    if os.path.exists(requests_file):
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
    
    requests.append({
        'clubId': data['clubId'],
        'reason': data['reason'],
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    with open(requests_file, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/clubs/apply', methods=['POST'])
def apply_club():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'teacher':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    data = request.json
    # 保存申请到管理员审核队列
    applications_file = os.path.join(USER_DATA_DIR, 'club_applications.json')
    
    applications = []
    if os.path.exists(applications_file):
        with open(applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
    
    applications.append({
        'id': secrets.token_urlsafe(8),
        'name': data['name'],
        'description': data['description'],
        'type': data['type'],
        'reason': data['reason'],
        'applicant': data['applicant'],
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    with open(applications_file, 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/clubs/applications', methods=['GET'])
def get_club_applications():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    applications_file = os.path.join(USER_DATA_DIR, 'club_applications.json')
    applications = []
    if os.path.exists(applications_file):
        with open(applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
    
    return jsonify({'success': True, 'applications': applications})

@app.route('/api/clubs/applications/<app_id>/approve', methods=['POST'])
def approve_club_application(app_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    applications_file = os.path.join(USER_DATA_DIR, 'club_applications.json')
    applications = []
    if os.path.exists(applications_file):
        with open(applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
    
    app = next((a for a in applications if a['id'] == app_id), None)
    if app:
        app['status'] = 'approved'
        with open(applications_file, 'w', encoding='utf-8') as f:
            json.dump(applications, f, ensure_ascii=False, indent=2)
        
        # 创建社团到独立数据库
        clubs_file = os.path.join(USER_DATA_DIR, 'clubs.json')
        clubs = []
        if os.path.exists(clubs_file):
            with open(clubs_file, 'r', encoding='utf-8') as f:
                clubs = json.load(f)
        
        club_data = {
            'id': secrets.token_urlsafe(8),
            'name': app['name'],
            'description': app['description'],
            'type': app['type'],
            'advisor': app['applicant'],
            'memberCount': 0,
            'created_at': datetime.now().isoformat()
        }
        
        clubs.append(club_data)
        
        with open(clubs_file, 'w', encoding='utf-8') as f:
            json.dump(clubs, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/clubs/applications/<app_id>/reject', methods=['POST'])
def reject_club_application(app_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    applications_file = os.path.join(USER_DATA_DIR, 'club_applications.json')
    applications = []
    if os.path.exists(applications_file):
        with open(applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
    
    app = next((a for a in applications if a['id'] == app_id), None)
    if app:
        app['status'] = 'rejected'
        with open(applications_file, 'w', encoding='utf-8') as f:
            json.dump(applications, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/admin/messages', methods=['GET'])
def get_admin_messages():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403}), 403
    
    messages = []
    
    # 社团申请消息
    applications_file = os.path.join(USER_DATA_DIR, 'club_applications.json')
    if os.path.exists(applications_file):
        with open(applications_file, 'r', encoding='utf-8') as f:
            apps = json.load(f)
            pending_apps = [a for a in apps if a.get('status') == 'pending']
            for app in pending_apps:
                messages.append({
                    'title': '新社团申请',
                    'content': f"{app['name']} - 等待审批",
                    'created_at': app.get('created_at', datetime.now().isoformat()),
                    'read': False
                })
    
    # 意见反馈消息
    feedback_file = os.path.join(USER_DATA_DIR, 'feedback.json')
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedbacks = json.load(f)
            unread_feedbacks = [f for f in feedbacks if not f.get('read', False)]
            for fb in unread_feedbacks:
                messages.append({
                    'title': '用户反馈',
                    'content': fb.get('content', '')[:50] + '...',
                    'created_at': fb.get('created_at', datetime.now().isoformat()),
                    'read': False
                })
    
    messages.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    
    feedback_file = os.path.join(USER_DATA_DIR, 'feedback.json')
    feedbacks = []
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedbacks = json.load(f)
    
    feedbacks.append({
        'id': secrets.token_urlsafe(8),
        'name': data.get('name', '匿名'),
        'email': data.get('email', ''),
        'content': data.get('content', ''),
        'created_at': datetime.now().isoformat(),
        'read': False
    })
    
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '文件名为空'}), 400
    
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    
    # 根据文件类型选择目录
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        # 检查是否为头像上传
        upload_type = request.form.get('type', 'banner')
        if upload_type == 'avatar':
            upload_dir = os.path.join('user_data', 'avatars')
            url_prefix = '/user_data/avatars/'
        else:
            upload_dir = os.path.join('image', 'banners')
            url_prefix = '/image/banners/'
    elif ext in ['.mp4', '.webm', '.ogg']:
        upload_dir = os.path.join('image', 'banners')
        url_prefix = '/image/banners/'
    else:
        upload_dir = os.path.join('news', 'images')
        url_prefix = '/news/images/'
    
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return jsonify({'success': True, 'url': url_prefix + filename})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
