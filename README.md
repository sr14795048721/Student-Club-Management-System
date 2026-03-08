# 社团管理系统

一个基于 Flask + SQLite 的现代化社团管理系统，采用华中师范大学风格设计。

## 功能特性

### 用户管理
- 多角色支持（管理员、教师、学生）
- 安全的用户认证和会话管理
- 独立的用户数据存储空间
- 完善的权限控制系统

### 系统功能
- 📰 新闻资讯管理
- 🎨 轮播图配置
- 📊 数据统计分析
- 👥 用户管理
- 🔐 登录状态检测
- 📁 独立用户数据存储

### 界面特点
- 响应式设计，支持多端访问
- 华中师范大学风格主题
- 全屏轮播展示
- 动画效果增强用户体验

## 技术栈

### 后端
- Python 3.8+
- Flask 2.0+
- SQLite 3
- Flask-CORS

### 前端
- HTML5 / CSS3 / JavaScript
- Bootstrap 3.3.7
- jQuery 3.6.0
- Slick Carousel
- Font Awesome 6.0
- Animate.css

## 快速开始

### 环境要求
- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd society
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python server.py
```
首次运行会自动创建数据库和默认管理员账户。

4. 启动服务
```bash
python server.py
```

5. 访问系统
打开浏览器访问：`http://localhost:5000`

### 默认账户
- 用户名：`admin`
- 密码：`admin123`
- 角色：管理员

**⚠️ 首次登录后请立即修改默认密码！**

## 项目结构

```
society/
├── server.py                 # Flask 后端服务
├── index.html               # 首页
├── requirements.txt         # Python 依赖
├── society_system.db        # SQLite 数据库
├── README.md               # 项目文档
├── HelpDocument/           # 帮助文档
│   ├── CONFIG.md          # 配置说明
│   ├── DEPLOYMENT.md      # 部署指南
│   └── NEWS_MANAGEMENT.md # 新闻管理
├── image/                  # 图片资源
│   ├── banners/           # 轮播图
│   ├── log.image/         # 登录页图片
│   └── main/              # 主要图片
├── news/                   # 新闻页面
│   ├── images/            # 新闻图片
│   ├── detail.html        # 新闻详情模板
│   └── *.html             # 新闻页面
├── page/                   # 页面文件
│   ├── log_system/        # 登录注册系统
│   │   ├── login.main.html
│   │   ├── register.html
│   │   └── *.js
│   ├── user_system/       # 用户系统
│   │   ├── admin/         # 管理员界面
│   │   ├── teacher/       # 教师界面
│   │   └── student/       # 学生界面
│   ├── auth-check.js      # 登录状态检测
│   ├── api-client.js      # API 客户端
│   └── backend.js         # 后端交互
└── user_data/             # 用户数据目录
    ├── banners.json       # 轮播配置
    └── {user_id}/         # 用户独立数据
        ├── profile.json   # 用户资料
        ├── clubs/         # 社团数据
        └── activities/    # 活动数据
```

## API 接口

### 认证接口
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/check-session` - 检查会话状态

### 用户接口
- `GET /api/users` - 获取用户列表（管理员）
- `GET /api/user/<id>/data` - 获取用户数据
- `POST /api/user/<id>/data` - 保存用户数据

### 新闻接口
- `GET /api/news` - 获取新闻列表
- `POST /api/news` - 创建新闻（管理员）
- `GET /api/news/<id>` - 获取新闻详情
- `PUT /api/news/<id>` - 更新新闻（管理员）
- `DELETE /api/news/<id>` - 删除新闻（管理员）

### 系统接口
- `GET /api/stats` - 获取访问统计
- `GET /api/admin/stats` - 获取系统统计（管理员）
- `GET /api/banners` - 获取轮播配置
- `POST /api/banners` - 保存轮播配置（管理员）
- `POST /api/upload` - 文件上传

## 安全特性

### 会话管理
- 基于 Token 的认证机制
- 会话自动过期（2小时）
- HttpOnly Cookie 防止 XSS
- CSRF 保护

### 权限控制
- 角色基础访问控制（RBAC）
- API 级别权限验证
- 前端路由保护
- 独立用户数据隔离

### 数据安全
- 密码哈希存储（Werkzeug）
- SQL 注入防护
- 文件上传验证
- 敏感信息加密

## 配置说明

### 数据库配置
数据库文件：`society_system.db`
- 自动初始化
- 包含用户、会话、访问记录、新闻等表

### 会话配置
在 `server.py` 中修改：
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 会话时长
app.secret_key = secrets.token_hex(32)  # 密钥
```

### 文件上传
支持的文件类型：
- 图片：jpg, jpeg, png, gif, webp
- 视频：mp4, webm, ogg

上传目录：
- 轮播图：`image/banners/`
- 新闻图片：`news/images/`

## 部署指南

### 开发环境
```bash
python server.py
```

### 生产环境
推荐使用 Gunicorn + Nginx：

1. 安装 Gunicorn
```bash
pip install gunicorn
```

2. 启动服务
```bash
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

3. 配置 Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/society;
    }
}
```

详细部署说明请参考：[DEPLOYMENT.md](HelpDocument/DEPLOYMENT.md)

## 常见问题

### 1. 数据库初始化失败
确保有写入权限，删除 `society_system.db` 后重新运行。

### 2. 登录后跳转失败
检查浏览器控制台，确认 Token 已保存到 localStorage。

### 3. 文件上传失败
检查目录权限，确保 `image/` 和 `news/` 目录可写。

### 4. 会话频繁过期
调整 `PERMANENT_SESSION_LIFETIME` 配置。

## 开发指南

### 添加新功能
1. 在 `server.py` 添加 API 路由
2. 在对应用户界面添加前端代码
3. 更新 `auth-check.js` 添加权限检查

### 自定义样式
主要样式文件：
- `index.html` - 首页样式
- `page/log_system/*.html` - 登录页样式
- `page/user_system/*/` - 用户界面样式

### 数据库迁移
修改表结构后需要：
1. 备份现有数据
2. 删除 `society_system.db`
3. 重新运行 `server.py` 初始化
4. 恢复数据

## 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 完整的用户认证系统
- ✅ 独立用户数据存储
- ✅ 登录状态检测
- ✅ 新闻管理功能
- ✅ 轮播图配置
- ✅ 数据统计分析
- ✅ 响应式界面设计

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交规范
- feat: 新功能
- fix: 修复问题
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

## 许可证

本项目仅供学习交流使用。

## 联系方式

- 📧 Email: 1804457646@qq.com
- 📱 Phone: 14795048721
- 📍 Address: 固原市原州区

## 致谢

- Bootstrap - UI 框架
- Flask - Web 框架
- 所有开源项目贡献者

---

**⚠️ 重要提示**
- 生产环境请修改默认密码
- 定期备份数据库
- 启用 HTTPS 加密传输
- 配置防火墙规则
