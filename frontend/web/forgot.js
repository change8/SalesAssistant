const TOKEN_STORAGE_KEY = 'sa_auth_token';

const requestForm = document.getElementById('reset-request-form');
const requestMessage = document.getElementById('reset-request-message');
const confirmForm = document.getElementById('reset-confirm-form');
const confirmMessage = document.getElementById('reset-confirm-message');
const resetTokenInput = document.getElementById('reset-token');

const PHONE_PATTERN = /^1[3-9]\d{9}$/;

function saveToken(token, expiresInSeconds) {
  const payload = {
    token,
    expiresAt: Date.now() + expiresInSeconds * 1000,
  };
  localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(payload));
}

function setMessage(target, text, type = 'info') {
  if (!target) return;
  target.textContent = text || '';
  target.className = type;
}

requestForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const phone = (document.getElementById('reset-phone').value || '').trim();
  if (!PHONE_PATTERN.test(phone)) {
    setMessage(requestMessage, '请输入 11 位有效手机号', 'error');
    return;
  }
  setMessage(requestMessage, '正在提交请求...', 'info');
  try {
    const response = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || '请求失败');
    }
    const data = await response.json();
    if (data?.reset_token) {
      resetTokenInput.value = data.reset_token;
      setMessage(
        requestMessage,
        `重置令牌：${data.reset_token}（有效期至 ${new Date(data.expires_at).toLocaleTimeString()}）`,
        'success',
      );
    } else {
      setMessage(requestMessage, '已发送找回请求，请留意短信通知。', 'success');
    }
  } catch (error) {
    console.error(error);
    setMessage(requestMessage, error.message || '发送失败', 'error');
  }
});

confirmForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const phone = (document.getElementById('reset-confirm-phone').value || '').trim();
  const token = (resetTokenInput.value || '').trim();
  const password = document.getElementById('reset-password').value || '';
  const confirmPassword = document.getElementById('reset-password-confirm').value || '';

  if (!PHONE_PATTERN.test(phone)) {
    setMessage(confirmMessage, '请输入 11 位有效手机号', 'error');
    return;
  }
  if (!token) {
    setMessage(confirmMessage, '请输入重置令牌', 'error');
    return;
  }
  if (password.length < 8 || !/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    setMessage(confirmMessage, '密码需至少 8 位并包含字母和数字', 'error');
    return;
  }
  if (password !== confirmPassword) {
    setMessage(confirmMessage, '两次输入的密码不一致', 'error');
    return;
  }

  setMessage(confirmMessage, '正在重置密码...', 'info');
  try {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, reset_token: token, new_password: password }),
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || '重置失败');
    }
    const data = await response.json();
    if (data?.access_token) {
      saveToken(data.access_token, data.expires_in || 3600);
      setMessage(confirmMessage, '密码已更新，正在跳转...', 'success');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 800);
    } else {
      setMessage(confirmMessage, '密码已更新，请返回登录页面', 'success');
    }
  } catch (error) {
    console.error(error);
    setMessage(confirmMessage, error.message || '操作失败', 'error');
  }
});
