// 社团管理系统后端逻辑脚本
const SystemBackend = {
  // 初始化系统数据
  init() {
    if (!localStorage.getItem('systemUsers')) {
      this.initDefaultData();
    }
  },

  // 初始化默认数据
  initDefaultData() {
    const defaultUsers = [
      { id: 1, username: 'admin', password: 'admin123', name: '系统管理员', role: 'admin', email: 'admin@system.com', phone: '13800138000', status: 'active' },
      { id: 2, username: 'teacher1', password: 'teacher123', name: '张老师', role: 'teacher', email: 'teacher1@school.com', phone: '13800138001', status: 'active' },
      { id: 3, username: 'student1', password: 'student123', name: '李明', role: 'student', email: 'student1@school.com', phone: '13800138002', status: 'active' }
    ];

    const defaultClubs = [
      { id: 1, name: '篮球社', category: '体育', description: '热爱篮球的同学聚集地', leader: '李明', members: ['李明', '王强', '张伟'], status: 'active', createTime: '2024-01-15' },
      { id: 2, name: '音乐社', category: '艺术', description: '音乐爱好者的天堂', leader: '王芳', members: ['王芳', '李娜'], status: 'active', createTime: '2024-01-20' },
      { id: 3, name: '编程社', category: '科技', description: '代码改变世界', leader: '赵强', members: ['赵强', '刘洋', '陈晨'], status: 'active', createTime: '2024-02-01' }
    ];

    const defaultActivities = [
      { id: 1, name: '篮球友谊赛', club: '篮球社', startTime: '2024-06-15T14:00', endTime: '2024-06-15T17:00', location: '体育馆', description: '与兄弟院校的友谊赛', maxParticipants: 50, participants: [], status: 'upcoming' },
      { id: 2, name: '音乐会', club: '音乐社', startTime: '2024-06-20T19:00', endTime: '2024-06-20T21:00', location: '大礼堂', description: '年度音乐盛典', maxParticipants: 200, participants: [], status: 'upcoming' }
    ];

    localStorage.setItem('systemUsers', JSON.stringify(defaultUsers));
    localStorage.setItem('systemClubs', JSON.stringify(defaultClubs));
    localStorage.setItem('systemActivities', JSON.stringify(defaultActivities));
  },

  // 用户登录
  login(username, password) {
    const users = JSON.parse(localStorage.getItem('systemUsers') || '[]');
    const user = users.find(u => u.username === username && u.password === password);
    
    if (!user) {
      return { success: false, message: '用户名或密码错误' };
    }

    if (user.status !== 'active') {
      return { success: false, message: '账户已被禁用' };
    }

    // 创建会话
    const session = {
      userId: user.id,
      username: user.username,
      name: user.name,
      role: user.role,
      loginTime: new Date().toISOString(),
      token: this.generateToken()
    };

    localStorage.setItem('currentSession', JSON.stringify(session));
    this.logActivity('login', `用户 ${user.name} 登录系统`);

    return { success: true, user: session };
  },

  // 用户注册
  register(userData) {
    const users = JSON.parse(localStorage.getItem('systemUsers') || '[]');
    
    if (users.find(u => u.username === userData.username)) {
      return { success: false, message: '用户名已存在' };
    }

    if (users.find(u => u.email === userData.email)) {
      return { success: false, message: '邮箱已被注册' };
    }

    const newUser = {
      id: Date.now(),
      ...userData,
      status: 'active',
      createTime: new Date().toISOString()
    };

    users.push(newUser);
    localStorage.setItem('systemUsers', JSON.stringify(users));
    this.logActivity('register', `新用户 ${newUser.name} 注册`);

    return { success: true, message: '注册成功' };
  },

  // 用户登出
  logout() {
    const session = this.getCurrentSession();
    if (session) {
      this.logActivity('logout', `用户 ${session.name} 退出系统`);
    }
    localStorage.removeItem('currentSession');
  },

  // 获取当前会话
  getCurrentSession() {
    const session = localStorage.getItem('currentSession');
    return session ? JSON.parse(session) : null;
  },

  // 检查权限
  checkPermission(requiredRole) {
    const session = this.getCurrentSession();
    if (!session) return false;

    const roleLevel = { admin: 3, teacher: 2, student: 1 };
    return roleLevel[session.role] >= roleLevel[requiredRole];
  },

  // 生成令牌
  generateToken() {
    return 'token_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  },

  // 记录活动日志
  logActivity(type, description) {
    const logs = JSON.parse(localStorage.getItem('systemLogs') || '[]');
    logs.push({
      id: Date.now(),
      type,
      description,
      timestamp: new Date().toISOString()
    });
    localStorage.setItem('systemLogs', JSON.stringify(logs.slice(-100))); // 保留最近100条
  },

  // 用户管理
  users: {
    getAll() {
      return JSON.parse(localStorage.getItem('systemUsers') || '[]');
    },
    
    getById(id) {
      const users = this.getAll();
      return users.find(u => u.id === id);
    },
    
    create(userData) {
      const users = this.getAll();
      const newUser = { id: Date.now(), ...userData, createTime: new Date().toISOString() };
      users.push(newUser);
      localStorage.setItem('systemUsers', JSON.stringify(users));
      SystemBackend.logActivity('user_create', `创建用户 ${newUser.name}`);
      return newUser;
    },
    
    update(id, userData) {
      const users = this.getAll();
      const index = users.findIndex(u => u.id === id);
      if (index !== -1) {
        users[index] = { ...users[index], ...userData };
        localStorage.setItem('systemUsers', JSON.stringify(users));
        SystemBackend.logActivity('user_update', `更新用户 ${users[index].name}`);
        return users[index];
      }
      return null;
    },
    
    delete(id) {
      const users = this.getAll();
      const filtered = users.filter(u => u.id !== id);
      localStorage.setItem('systemUsers', JSON.stringify(filtered));
      SystemBackend.logActivity('user_delete', `删除用户 ID: ${id}`);
    }
  },

  // 社团管理
  clubs: {
    getAll() {
      return JSON.parse(localStorage.getItem('systemClubs') || '[]');
    },
    
    getById(id) {
      const clubs = this.getAll();
      return clubs.find(c => c.id === id);
    },
    
    create(clubData) {
      const clubs = this.getAll();
      const newClub = { id: Date.now(), ...clubData, createTime: new Date().toISOString() };
      clubs.push(newClub);
      localStorage.setItem('systemClubs', JSON.stringify(clubs));
      SystemBackend.logActivity('club_create', `创建社团 ${newClub.name}`);
      return newClub;
    },
    
    update(id, clubData) {
      const clubs = this.getAll();
      const index = clubs.findIndex(c => c.id === id);
      if (index !== -1) {
        clubs[index] = { ...clubs[index], ...clubData };
        localStorage.setItem('systemClubs', JSON.stringify(clubs));
        SystemBackend.logActivity('club_update', `更新社团 ${clubs[index].name}`);
        return clubs[index];
      }
      return null;
    },
    
    delete(id) {
      const clubs = this.getAll();
      const filtered = clubs.filter(c => c.id !== id);
      localStorage.setItem('systemClubs', JSON.stringify(filtered));
      SystemBackend.logActivity('club_delete', `删除社团 ID: ${id}`);
    }
  },

  // 活动管理
  activities: {
    getAll() {
      return JSON.parse(localStorage.getItem('systemActivities') || '[]');
    },
    
    getById(id) {
      const activities = this.getAll();
      return activities.find(a => a.id === id);
    },
    
    create(activityData) {
      const activities = this.getAll();
      const newActivity = { id: Date.now(), ...activityData, createTime: new Date().toISOString(), participants: [] };
      activities.push(newActivity);
      localStorage.setItem('systemActivities', JSON.stringify(activities));
      SystemBackend.logActivity('activity_create', `创建活动 ${newActivity.name}`);
      return newActivity;
    },
    
    update(id, activityData) {
      const activities = this.getAll();
      const index = activities.findIndex(a => a.id === id);
      if (index !== -1) {
        activities[index] = { ...activities[index], ...activityData };
        localStorage.setItem('systemActivities', JSON.stringify(activities));
        SystemBackend.logActivity('activity_update', `更新活动 ${activities[index].name}`);
        return activities[index];
      }
      return null;
    },
    
    delete(id) {
      const activities = this.getAll();
      const filtered = activities.filter(a => a.id !== id);
      localStorage.setItem('systemActivities', JSON.stringify(filtered));
      SystemBackend.logActivity('activity_delete', `删除活动 ID: ${id}`);
    },
    
    register(activityId, userId) {
      const activities = this.getAll();
      const activity = activities.find(a => a.id === activityId);
      if (activity && !activity.participants.includes(userId)) {
        activity.participants.push(userId);
        localStorage.setItem('systemActivities', JSON.stringify(activities));
        SystemBackend.logActivity('activity_register', `用户 ${userId} 报名活动 ${activity.name}`);
        return { success: true };
      }
      return { success: false, message: '报名失败' };
    },
    
    unregister(activityId, userId) {
      const activities = this.getAll();
      const activity = activities.find(a => a.id === activityId);
      if (activity) {
        activity.participants = activity.participants.filter(p => p !== userId);
        localStorage.setItem('systemActivities', JSON.stringify(activities));
        SystemBackend.logActivity('activity_unregister', `用户 ${userId} 取消报名活动 ${activity.name}`);
        return { success: true };
      }
      return { success: false, message: '取消失败' };
    }
  },

  // 统计数据
  statistics: {
    getOverview() {
      const users = SystemBackend.users.getAll();
      const clubs = SystemBackend.clubs.getAll();
      const activities = SystemBackend.activities.getAll();
      
      return {
        userCount: users.length,
        clubCount: clubs.length,
        activityCount: activities.length,
        activeUsers: users.filter(u => u.status === 'active').length,
        upcomingActivities: activities.filter(a => a.status === 'upcoming').length
      };
    },
    
    getUsersByRole() {
      const users = SystemBackend.users.getAll();
      return {
        admin: users.filter(u => u.role === 'admin').length,
        teacher: users.filter(u => u.role === 'teacher').length,
        student: users.filter(u => u.role === 'student').length
      };
    },
    
    getActivityTrend() {
      const activities = SystemBackend.activities.getAll();
      const months = {};
      activities.forEach(a => {
        if (a.startTime) {
          const month = new Date(a.startTime).getMonth() + 1;
          months[month] = (months[month] || 0) + 1;
        }
      });
      return months;
    }
  }
};

// 初始化系统
SystemBackend.init();
