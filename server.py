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
    role = data.get('role', 'student')
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
    
    if user[6] != 'active':
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
            'email': user[5]
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

@app.route('/api/user/<int:user_id>/data', methods=['GET', 'POST'])
def user_data(user_id):
    user, error = check_session()
    if error:
        return jsonify(error), error['code']
    
    if user['id'] != user_id and user['role'] != 'admin':
        return jsonify({'error': 'PERMISSION_DENIED', 'code': 403, 'message': '权限不足'}), 403
    
    user_dir = os.path.join(USER_DATA_DIR, str(user_id))
    data_type = request.args.get('type', 'profile')
    file_path = os.path.join(user_dir, f'{data_type}.json')
    
    if request.method == 'GET':
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify({'success': True, 'data': json.load(f)})
        return jsonify({'success': True, 'data': {}})
    
    elif request.method == 'POST':
        data = request.json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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
    
    # 数据库大小
    import os
    db_size = os.path.getsize(DB_PATH) / 1024 / 1024  # MB
    
    conn.close()
    
    # 系统信息
    import psutil
    import platform
    
    return jsonify({
        'success': True,
        'stats': {
            'users': {
                'total': user_count,
                'active': active_users,
                'inactive': user_count - active_users
            },
            'visits': {
                'total': total_visits,
                'unique': unique_visitors,
                'today': today_visits
            },
            'sessions': {
                'active': active_sessions
            },
            'system': {
                'db_size': round(db_size, 2),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'platform': platform.system(),
                'python_version': platform.python_version()
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
        if user['role'] != 'admin':
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
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    
    # 根据文件类型选择目录
    if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        upload_dir = os.path.join('image', 'banners')
        url_prefix = '/image/banners/'
    elif ext.lower() in ['.mp4', '.webm', '.ogg']:
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
