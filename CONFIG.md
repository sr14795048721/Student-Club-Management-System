# 前后端配置说明

## 路由配置

### 后端路由 (server.py)
- `/` - 首页展示页面 (index.html)
- `/login` - 登录页面
- `/register` - 注册页面
- `/home` - 首页 (同 `/`)
- `/page/<path>` - 静态页面资源
- `/image/<path>` - 图片资源

### API路由
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录 (支持用户名或邮箱)
- `POST /api/logout` - 用户登出
- `GET /api/check-session` - 检查会话
- `GET /api/users` - 获取用户列表 (管理员)
- `GET /api/user/{id}/data` - 获取用户数据
- `POST /api/user/{id}/data` - 保存用户数据

## 页面跳转逻辑

### 登录后跳转
根据用户角色跳转到不同页面：
- **admin** → `/page/user_system/admin/admin.html`
- **teacher** → `/page/user_system/teacher/`
- **student** → `/page/user_system/student/`

### 会话检查
- 公开页面：`/`, `/login`, `/register`
- 其他页面：需要登录，未登录自动跳转到 `/login`

## 启动流程

1. 启动服务器：
```bash
python server.py
```

2. 访问地址：
- 首页：http://localhost:5000/
- 登录：http://localhost:5000/login

3. 默认账户：
- 用户名：admin
- 邮箱：admin@system.com
- 密码：admin123

## 文件说明

### 前端核心文件
- `index.html` - 首页展示页面
- `page/log_system/login.main.html` - 登录页面
- `page/api-client.js` - API客户端 (连接Python后端)
- `page/log_system/login-handler.js` - 登录表单处理

### 后端核心文件
- `server.py` - Flask后端服务
- `society_system.db` - SQLite数据库
- `user_data/` - 用户数据目录

## 注意事项

1. **不要使用 backend.js**
   - `backend.js` 是前端模拟系统，使用localStorage
   - 实际部署使用 `api-client.js` 连接Python后端

2. **路径统一**
   - 所有内部链接使用 `/login` 而非 `page/log_system/login.main.html`
   - 页面中的资源引用使用绝对路径 `/page/` 或 `/image/`
   - 不要使用相对路径 `../` 或 `./`

3. **会话管理**
   - Token存储在localStorage
   - 会话有效期2小时
   - 自动检查会话状态
