// admin_data.js - 管理后台数据处理模块
(function(global) {
  const STORAGE_KEYS = {
    users: 'systemUsers',
    clubs: 'systemClubs',
    activities: 'systemActivities',
    notifications: 'systemNotifications'
  };

  // 初始化默认数据
  function initDefaultData() {
    if (!localStorage.getItem(STORAGE_KEYS.users)) {
      localStorage.setItem(STORAGE_KEYS.users, JSON.stringify([]));
    }
    if (!localStorage.getItem(STORAGE_KEYS.clubs)) {
      localStorage.setItem(STORAGE_KEYS.clubs, JSON.stringify([]));
    }
    if (!localStorage.getItem(STORAGE_KEYS.activities)) {
      localStorage.setItem(STORAGE_KEYS.activities, JSON.stringify([]));
    }
    if (!localStorage.getItem(STORAGE_KEYS.notifications)) {
      localStorage.setItem(STORAGE_KEYS.notifications, JSON.stringify([]));
    }
  }

  // 获取统计数据
  function getStats() {
    initDefaultData();
    
    const users = JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || '[]');
    const clubs = JSON.parse(localStorage.getItem(STORAGE_KEYS.clubs) || '[]');
    const activities = JSON.parse(localStorage.getItem(STORAGE_KEYS.activities) || '[]');
    const notifications = JSON.parse(localStorage.getItem(STORAGE_KEYS.notifications) || '[]');
    
    const pendingNotifications = notifications.filter(n => n.status === 'pending').length;
    
    return {
      userCount: users.length,
      clubCount: clubs.length,
      activityCount: activities.length,
      notificationCount: pendingNotifications
    };
  }

  // 更新统计数据
  function updateStats(type, count) {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEYS[type]) || '[]');
    if (count !== undefined) {
      // 模拟数据更新
      while (data.length < count) {
        data.push({ id: Date.now() + Math.random() });
      }
      while (data.length > count) {
        data.pop();
      }
      localStorage.setItem(STORAGE_KEYS[type], JSON.stringify(data));
    }
  }

  global.AdminData = {
    getStats,
    updateStats,
    initDefaultData
  };
})(window);
