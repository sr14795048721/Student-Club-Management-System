// 登录表单处理
async function handleLogin(e) {
  e.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  if (!email || !password) {
    alert('请输入邮箱和密码');
    return;
  }

  const btn = e.target.querySelector('.login-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 登录中...';

  try {
    const result = await ApiClient.login(email, password);
    
    if (result.success) {
      const role = result.user.role;
      alert('登录成功！');
      
      // 根据角色跳转到对应页面
      if (role === 'admin') {
        window.location.href = '/page/user_system/admin/admin.html';
      } else if (role === 'teacher') {
        window.location.href = '/page/user_system/teacher/';
      } else {
        window.location.href = '/page/user_system/student/';
      }
    } else {
      alert(result.message || '登录失败');
    }
  } catch (error) {
    alert('登录失败: ' + error.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>登录</span><i class="fas fa-arrow-right"></i>';
  }
}

// 注册表单处理
async function handleRegister(e) {
  e.preventDefault();
  
  const username = document.getElementById('username').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (password !== confirmPassword) {
    alert('两次密码输入不一致');
    return;
  }

  const btn = e.target.querySelector('.login-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 注册中...';

  try {
    const result = await ApiClient.register({
      username,
      email,
      password,
      name: username,
      role: 'student'
    });
    
    if (result.success) {
      alert('注册成功！请登录');
      switchToLogin(new Event('click'));
    } else {
      alert(result.message || '注册失败');
    }
  } catch (error) {
    alert('注册失败: ' + error.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>注册</span><i class="fas fa-arrow-right"></i>';
  }
}
