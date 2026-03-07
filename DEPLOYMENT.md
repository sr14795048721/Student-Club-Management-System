# 社团管理系统 - 部署测试指南

## 系统状态

✅ **服务器运行正常**
- Flask后端已启动
- 端口：5000
- 支持局域网访问

## 快速测试

### 1. 本地访问
```
http://localhost:5000/          # 首页
http://localhost:5000/login     # 登录页
```

### 2. 局域网访问
```
http://192.168.1.x:5000/        # 首页
http://192.168.1.x:5000/login   # 登录页
```

### 3. 测试账户
```
用户名: admin
邮箱: admin@system.com
密码: admin123
角色: 管理员
```

## 功能测试清单

### ✅ 已完成配置
- [x] 后端服务器启动
- [x] 数据库初始化
- [x] 用户认证API
- [x] 会话管理
- [x] 静态文件服务
- [x] 路由配置
- [x] UTF-8编码
- [x] 缓存控制
- [x] CORS跨域

### 🔧 前端页面
- [x] 首页展示 (/)
- [x] 登录页面 (/login)
- [x] 管理后台 (/page/user_system/admin/admin.html)
- [ ] 教师页面 (待开发)
- [ ] 学生页面 (待开发)

### 📝 测试步骤

#### 1. 测试登录流程
1. 访问 http://localhost:5000/login
2. 输入邮箱：admin@system.com
3. 输入密码：admin123
4. 点击登录
5. 应跳转到管理后台

#### 2. 测试管理后台
1. 登录成功后自动跳转
2. 查看统计数据
3. 测试各功能菜单
4. 查看活动日历

#### 3. 测试退出登录
1. 点击右上角"退出登录"
2. 应跳转回登录页
3. Token已清除

## 常见问题

### Q1: 页面显示乱码
**解决方案：**
- 按 Ctrl+F5 强制刷新
- 清理浏览器缓存
- 重启服务器

### Q2: 登录后404错误
**解决方案：**
- 检查路径配置
- 确认文件存在
- 查看服务器日志

### Q3: 图片404错误（slide3-20）
**说明：** 这是正常现象
- 系统扫描slide1-5的图片
- 当前只有slide1.png和slide2.png
- 不影响功能使用

### Q4: 无法访问管理后台
**检查项：**
1. 是否使用admin账户登录
2. Token是否有效
3. 路径是否正确：/page/user_system/admin/admin.html

## 服务器日志说明

### 正常日志
```
OPTIONS /api/login HTTP/1.1" 200    # CORS预检请求
POST /api/login HTTP/1.1" 200       # 登录成功
GET /page/... HTTP/1.1" 200/304     # 页面加载
```

### 错误日志
```
404 - 文件不存在
401 - 未授权（需要登录）
403 - 权限不足
500 - 服务器错误
```

## 性能优化

### 已实现
- 禁用静态文件缓存（开发模式）
- UTF-8编码响应
- CORS跨域支持
- 会话超时管理

### 生产环境建议
1. 启用缓存（修改SEND_FILE_MAX_AGE_DEFAULT）
2. 使用HTTPS
3. 配置反向代理（Nginx）
4. 使用生产级WSGI服务器（Gunicorn）
5. 数据库迁移到MySQL/PostgreSQL

## 下一步开发

### 待完成功能
1. 教师管理页面
2. 学生管理页面
3. 社团详细管理
4. 活动报名系统
5. 通知推送功能
6. 数据统计图表
7. 文件上传功能
8. 权限细化管理

### 优化项
1. 前端表单验证增强
2. 错误提示优化
3. 加载动画
4. 响应式布局完善
5. 图片懒加载

## 维护命令

### 启动服务器
```bash
python server.py
```

### 查看账户
```bash
python view_accounts.py
```

### 清理缓存
```bash
clear_cache.bat  # Windows
```

### 检查路径
```bash
python check_paths.py
```

## 技术栈

### 后端
- Python 3.x
- Flask 2.x
- SQLite3
- Flask-CORS

### 前端
- HTML5/CSS3
- JavaScript (ES6+)
- Swiper.js
- Font Awesome

### 数据存储
- SQLite数据库（用户、会话）
- JSON文件（用户数据）
- localStorage（前端缓存）

## 联系支持

如遇问题，请检查：
1. Python版本 >= 3.7
2. 依赖包已安装（requirements.txt）
3. 端口5000未被占用
4. 防火墙允许访问

---
最后更新：2026-03-07
版本：v1.0
