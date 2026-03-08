# 新闻管理系统使用说明

## 功能概述

新闻管理系统允许管理员发布、编辑和管理社团新闻，首页自动从数据库加载最新新闻并展示。

## 主要功能

### 1. 新闻发布
- 管理员可以通过富文本编辑器创建新闻
- 支持上传封面图片
- 可设置发布日期
- 自动记录作者和创建时间

### 2. 新闻编辑
- 修改新闻标题、内容、封面
- 更新发布日期
- 自动记录更新时间

### 3. 新闻删除
- 管理员可删除不需要的新闻
- 删除操作需要确认

### 4. 自动展示
- 首页自动从API加载最新新闻
- 轮播图展示前3条新闻
- 列表展示所有已发布新闻
- 自动统计浏览量

## 使用步骤

### 初始化示例数据

```bash
python init_news.py
```

这将创建5条示例新闻数据。

### 访问新闻管理

1. 登录管理员账户（默认：admin/admin123）
2. 进入管理后台
3. 点击"新闻管理"菜单
4. 可以查看、编辑、删除现有新闻，或发布新新闻

### 发布新闻

1. 点击"发布新闻"按钮
2. 填写新闻标题
3. 上传封面图片（可选）
4. 选择发布日期
5. 使用富文本编辑器编写新闻内容
6. 点击"保存"按钮

### 编辑新闻

1. 在新闻列表中找到要编辑的新闻
2. 点击"编辑"按钮
3. 修改相关信息
4. 点击"保存"按钮

## 文件结构

```
society/
├── news/                          # 新闻存储目录
│   ├── images/                    # 新闻图片存储
│   └── detail.html                # 新闻详情页模板
├── page/
│   └── user_system/
│       └── admin/
│           └── news_manage.html   # 新闻管理页面
├── server.py                      # 后端API（已添加新闻接口）
└── init_news.py                   # 示例数据初始化脚本
```

## API接口

### 获取新闻列表
```
GET /api/news
返回所有已发布的新闻
```

### 获取新闻详情
```
GET /api/news/<id>
返回指定ID的新闻详情，并增加浏览量
```

### 创建新闻（需要管理员权限）
```
POST /api/news
Body: {
  "title": "新闻标题",
  "content": "新闻内容（HTML格式）",
  "cover_image": "封面图片URL",
  "publish_date": "2025-01-20",
  "status": "published"
}
```

### 更新新闻（需要管理员权限）
```
PUT /api/news/<id>
Body: 同创建新闻
```

### 删除新闻（需要管理员权限）
```
DELETE /api/news/<id>
```

### 上传图片（需要登录）
```
POST /api/upload
Content-Type: multipart/form-data
Body: file=<图片文件>
返回: {"success": true, "url": "/news/images/xxx.jpg"}
```

## 数据库表结构

```sql
CREATE TABLE news (
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
);
```

## 注意事项

1. 只有管理员可以创建、编辑和删除新闻
2. 新闻内容支持HTML格式，可以包含图片、链接等
3. 封面图片会自动存储在 `news/images/` 目录
4. 首页会自动刷新显示最新新闻，无需手动配置
5. 新闻详情页使用统一模板，通过API动态加载内容
6. 浏览量会在每次访问新闻详情时自动增加

## 富文本编辑器功能

- 文本格式化（粗体、斜体）
- 段落对齐
- 列表（有序、无序）
- 插入链接
- 插入图片
- 查看HTML源码

## 后续优化建议

1. 添加新闻分类功能
2. 支持新闻草稿保存
3. 添加新闻搜索功能
4. 支持新闻评论
5. 添加新闻标签系统
6. 支持定时发布
