// 登录状态检查 - 增强版
(async function() {
  const path = window.location.pathname;
  
  // 公开页面列表
  const publicPages = [
    '/',
    '/login',
    '/register',
    '/home',
    '/news'
  ];
  
  // 检查是否为公开页面
  const isPublicPage = publicPages.some(p => {
    if (p === '/news') {
      return path.startsWith('/news/');
    }
    return path === p || path.includes('/page/log_system/');
  });
  
  // 如果是用户系统页面，必须验证登录状态
  if (!isPublicPage && path.includes('/page/user_system/')) {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
      alert('未登录或会话已过期，请先登录');
      localStorage.removeItem('authToken');
      localStorage.removeItem('userInfo');
      window.location.href = '/login';
      return;
    }
    
    try {
      const res = await fetch('/api/check-session', {
        headers: { 'Authorization': token },
        cache: 'no-cache'
      });
      
      if (!res.ok) {
        throw new Error('Session check failed');
      }
      
      const data = await res.json();
      
      if (!data.success || !data.user) {
        alert(data.message || '会话已过期，请重新登录');
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        window.location.href = '/login';
        return;
      }
      
      // 验证角色权限
      const userRole = data.user.role;
      const requiredRole = path.includes('/admin/') ? 'admin' :
                          path.includes('/teacher/') ? 'teacher' :
                          path.includes('/student/') ? 'student' : null;
      
      if (requiredRole && userRole !== requiredRole && userRole !== 'admin') {
        alert('权限不足，无法访问该页面');
        // 根据角色跳转到对应页面
        const rolePages = {
          'admin': '/page/user_system/admin/admin.html',
          'teacher': '/page/user_system/teacher/',
          'student': '/page/user_system/student/'
        };
        window.location.href = rolePages[userRole] || '/login';
        return;
      }
      
      // 更新本地用户信息
      localStorage.setItem('userInfo', JSON.stringify(data.user));
      
    } catch (err) {
      console.error('Auth check error:', err);
      alert('验证失败，请重新登录');
      localStorage.removeItem('authToken');
      localStorage.removeItem('userInfo');
      window.location.href = '/login';
    }
  }
  
  // 如果已登录用户访问登录/注册页面，自动跳转到对应界面
  if ((path === '/login' || path === '/register' || path.includes('/page/log_system/')) && 
      !path.includes('login.image.html')) {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const res = await fetch('/api/check-session', {
          headers: { 'Authorization': token },
          cache: 'no-cache'
        });
        const data = await res.json();
        
        if (data.success && data.user) {
          const rolePages = {
            'admin': '/page/user_system/admin/admin.html',
            'teacher': '/page/user_system/teacher/',
            'student': '/page/user_system/student/'
          };
          window.location.href = rolePages[data.user.role] || '/';
        }
      } catch (err) {
        // 验证失败，清除token
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
      }
    }
  }
})();
