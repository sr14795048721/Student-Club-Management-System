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

# 前端路由
@app.route('/')
def index():
    response = send_from_directory('.', 'index.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
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
    return send_from_directory('page', filename)

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
