// 登录状态检查
(async function() {
  const path = window.location.pathname;
  const publicPages = ['/', '/login', '/register', '/home'];
  const isPublicPage = publicPages.some(p => path === p || path.includes('/page/log_system/'));
  
  if (!isPublicPage && path.includes('/page/user_system/')) {
    const token = localStorage.getItem('authToken');
    if (!token) {
      alert('未登录或会话已过期，请先登录');
      window.location.href = '/login';
      return;
    }
    
    try {
      const res = await fetch('/api/check-session', {
        headers: { 'Authorization': token }
      });
      const data = await res.json();
      
      if (!data.success) {
        alert('会话已过期，请重新登录');
        localStorage.removeItem('authToken');
        window.location.href = '/login';
      }
    } catch (err) {
      alert('验证失败，请重新登录');
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
  }
})();
