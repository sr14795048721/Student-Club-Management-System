const apiClient = {
  async request(url, options = {}) {
    const headers = {
      'Authorization': localStorage.getItem('authToken'),
      ...options.headers
    };
    
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    if (response.status === 401) {
      alert('会话超时，请重新登录');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    
    return response;
  },
  
  async get(url) {
    return this.request(url);
  },
  
  async post(url, data, isJson = true) {
    return this.request(url, {
      method: 'POST',
      body: isJson ? JSON.stringify(data) : data
    });
  },
  
  async put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  async delete(url) {
    return this.request(url, {
      method: 'DELETE'
    });
  }
};

// API客户端 - 与Python后端通信
const API_BASE = 'http://localhost:5000/api';

const ApiClient = {
  token: localStorage.getItem('authToken'),

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = this.token;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.status === 401) {
        this.handleSessionTimeout(data);
        throw new Error(data.message || '会话超时');
      }

      if (!response.ok) {
        throw new Error(data.message || '请求失败');
      }

      return data;
    } catch (error) {
      console.error('API请求错误:', error);
      throw error;
    }
  },

  handleSessionTimeout(data) {
    this.setToken(null);
    const errorCode = data.code || 401;
    const errorType = data.error || 'SESSION_TIMEOUT';
    
    alert(`错误代码: ${errorCode}\n错误类型: ${errorType}\n${data.message || '会话超时，请重新登录'}`);
    
    setTimeout(() => {
      window.location.href = '/login';
    }, 1000);
  },

  async checkSession() {
    if (!this.token) {
      return { valid: false, user: null };
    }

    try {
      const data = await this.request('/check-session');
      return { valid: true, user: data.user };
    } catch (error) {
      return { valid: false, user: null };
    }
  },

  async login(usernameOrEmail, password) {
    const data = await this.request('/login', {
      method: 'POST',
      body: JSON.stringify({ username: usernameOrEmail, password })
    });

    if (data.success) {
      this.setToken(data.token);
    }

    return data;
  },

  async register(userData) {
    return await this.request('/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  async logout() {
    try {
      await this.request('/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  },

  async getUsers() {
    return await this.request('/users');
  },

  async getUserData(userId, type = 'profile') {
    return await this.request(`/user/${userId}/data?type=${type}`);
  },

  async saveUserData(userId, type, data) {
    return await this.request(`/user/${userId}/data?type=${type}`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};

// 页面加载时检查会话
window.addEventListener('DOMContentLoaded', async () => {
  const publicPages = ['/login', '/page/log_system/login.main.html', '/page/log_system/register.html', '/'];
  const currentPath = window.location.pathname;
  
  if (!publicPages.some(page => currentPath.includes(page) || currentPath === page)) {
    const session = await ApiClient.checkSession();
    if (!session.valid) {
      alert('错误代码: 401\n错误类型: SESSION_TIMEOUT\n会话超时，请重新登录');
      window.location.href = '/login';
    }
  }
});
