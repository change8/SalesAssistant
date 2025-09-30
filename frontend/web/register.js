const API_BASE = '';
const TOKEN_STORAGE_KEY = 'sa_auth_token';
const PHONE_PATTERN = /^1[3-9]\d{9}$/;

const form = document.getElementById('register-form');
const messageEl = document.getElementById('register-message');

function setMessage(message, type = 'info') {
  if (!messageEl) return;
  messageEl.textContent = message || '';
  messageEl.className = type;
}

function saveToken(token, expiresInSeconds) {
  const payload = {
    token,
    expiresAt: Date.now() + expiresInSeconds * 1000,
  };
  localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(payload));
}

async function safeError(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') {
      return payload.detail;
    }
    if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
      const first = payload.detail[0];
      const msg = first?.msg || first?.message;
      if (typeof msg === 'string') {
        return msg;
      }
    }
    return JSON.stringify(payload);
  } catch (error) {
    return response.statusText;
  }
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const phoneInput = document.getElementById('register-phone');
  const nameInput = document.getElementById('register-name');
  const pwdInput = document.getElementById('register-password');
  const confirmInput = document.getElementById('register-confirm');

  const phone = phoneInput?.value.trim() || '';
  const fullName = nameInput?.value.trim() || '';
  const password = pwdInput?.value || '';
  const confirmPassword = confirmInput?.value || '';

  if (!PHONE_PATTERN.test(phone)) {
    setMessage('请输入 11 位有效手机号', 'error');
    phoneInput?.focus();
    return;
  }
  if (password.length < 8) {
    setMessage('密码至少需要 8 位', 'error');
    pwdInput?.focus();
    return;
  }
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    setMessage('密码需包含字母和数字', 'error');
    pwdInput?.focus();
    return;
  }
  if (password !== confirmPassword) {
    setMessage('两次输入的密码不一致', 'error');
    confirmInput?.focus();
    return;
  }

  const payload = {
    phone,
    password,
    full_name: fullName || null,
  };

  try {
    setMessage('注册中...', 'info');
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await safeError(response));
    }

    const loginResp = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, password }),
    });
    if (!loginResp.ok) {
      throw new Error(await safeError(loginResp));
    }
    const data = await loginResp.json();
    saveToken(data.access_token, data.expires_in);
    setMessage('注册成功，正在跳转...', 'success');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 600);
  } catch (error) {
    console.error(error);
    setMessage(error.message || '注册失败，请稍后再试', 'error');
  }
});
