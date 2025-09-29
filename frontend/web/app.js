const API_BASE = '';
const TOKEN_STORAGE_KEY = 'sa_auth_token';
const DEFAULT_COST_RATES = {
  architect: 18000,
  project_manager: 16000,
  product_design: 12000,
  backend_dev: 15000,
  frontend_dev: 14000,
  qa: 11000,
  implementation: 10000,
};
const DEFAULT_RATIOS = {
  architect: 0.12,
  project_manager: 0.15,
};

const authSection = document.getElementById('auth-section');
const appSection = document.getElementById('app-section');
const authMessage = document.getElementById('auth-message');
const userInfoEl = document.getElementById('user-info');
const logoutBtn = document.getElementById('logout-btn');

const tenderResult = document.getElementById('tender-result');
const workloadResult = document.getElementById('workload-result');
const costingResult = document.getElementById('costing-result');

function setAuthMessage(message, type = 'info') {
  if (!authMessage) return;
  authMessage.textContent = message || '';
  authMessage.className = type;
}

function saveToken(token, expiresInSeconds) {
  const payload = {
    token,
    expiresAt: Date.now() + expiresInSeconds * 1000,
  };
  localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(payload));
}

function readToken() {
  const raw = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed.token || !parsed.expiresAt) return null;
    if (Date.now() > parsed.expiresAt) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      return null;
    }
    return parsed.token;
  } catch (error) {
    console.error('Invalid token payload', error);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    return null;
  }
}

function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function authFetch(path, options = {}) {
  const token = readToken();
  if (!token) {
    throw new Error('未登录或登录已过期');
  }
  const headers = new Headers(options.headers || {});
  headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (response.status === 401) {
    clearToken();
    showAuth();
    throw new Error('登录失效，请重新登录');
  }
  if (!response.ok) {
    const detail = await safeError(response);
    throw new Error(detail || '请求失败');
  }
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch (error) {
    return text;
  }
}

async function safeError(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') {
      return payload.detail;
    }
    return JSON.stringify(payload);
  } catch (error) {
    return response.statusText;
  }
}

function showApp(user) {
  authSection.classList.add('hidden');
  appSection.classList.remove('hidden');
  userInfoEl.textContent = `欢迎，${user.full_name || user.phone}`;
}

function showAuth() {
  appSection.classList.add('hidden');
  authSection.classList.remove('hidden');
  userInfoEl.textContent = '';
}

async function fetchProfile() {
  try {
    const me = await authFetch('/api/auth/me');
    if (me) {
      showApp(me);
    }
  } catch (error) {
    console.warn(error);
    showAuth();
  }
}

function initTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.dataset.target;
      document.querySelectorAll('.tab-panel').forEach((panel) => {
        panel.classList.toggle('hidden', panel.id !== targetId);
      });
    });
  });
}

function fillDefaultRates() {
  Object.entries(DEFAULT_COST_RATES).forEach(([role, value]) => {
    const input = document.getElementById(`rate-${role}`);
    if (input) input.value = value;
  });
  const architectRatio = document.getElementById('ratio-architect');
  const pmRatio = document.getElementById('ratio-project_manager');
  if (architectRatio) architectRatio.value = DEFAULT_RATIOS.architect;
  if (pmRatio) pmRatio.value = DEFAULT_RATIOS.project_manager;
}

function collectRates() {
  const rates = {};
  Object.keys(DEFAULT_COST_RATES).forEach((role) => {
    const input = document.getElementById(`rate-${role}`);
    const value = input && input.value ? Number(input.value) : DEFAULT_COST_RATES[role];
    rates[role] = Number.isFinite(value) && value > 0 ? value : DEFAULT_COST_RATES[role];
  });
  return rates;
}

function collectRatios() {
  const architectRatio = Number(document.getElementById('ratio-architect')?.value || DEFAULT_RATIOS.architect);
  const pmRatio = Number(document.getElementById('ratio-project_manager')?.value || DEFAULT_RATIOS.project_manager);
  return {
    architect_ratio: Number.isFinite(architectRatio) ? architectRatio : DEFAULT_RATIOS.architect,
    project_manager_ratio: Number.isFinite(pmRatio) ? pmRatio : DEFAULT_RATIOS.project_manager,
  };
}

function renderResult(target, data) {
  if (!target) return;
  if (data === null || data === undefined) {
    target.textContent = '暂无结果';
    return;
  }
  if (typeof data === 'string') {
    target.textContent = data;
    return;
  }
  target.textContent = JSON.stringify(data, null, 2);
}

function bindAuthForms() {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  loginForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    setAuthMessage('登录中...', 'info');
    const payload = {
      phone: document.getElementById('login-phone').value.trim(),
      password: document.getElementById('login-password').value,
    };
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await safeError(response));
      }
      const data = await response.json();
      saveToken(data.access_token, data.expires_in);
      setAuthMessage('登录成功', 'success');
      await fetchProfile();
    } catch (error) {
      console.error(error);
      setAuthMessage(error.message || '登录失败', 'error');
    }
  });

  registerForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    setAuthMessage('注册中...', 'info');
    const payload = {
      phone: document.getElementById('register-phone').value.trim(),
      password: document.getElementById('register-password').value,
      full_name: document.getElementById('register-name').value.trim() || null,
    };
    try {
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
        body: JSON.stringify({ phone: payload.phone, password: payload.password }),
      });
      if (!loginResp.ok) {
        throw new Error(await safeError(loginResp));
      }
      const data = await loginResp.json();
      saveToken(data.access_token, data.expires_in);
      setAuthMessage('注册成功，已自动登录', 'success');
      await fetchProfile();
    } catch (error) {
      console.error(error);
      setAuthMessage(error.message || '注册失败', 'error');
    }
  });
}

function bindTenderForms() {
  const textForm = document.getElementById('tender-text-form');
  const fileForm = document.getElementById('tender-file-form');

  textForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    tenderResult.textContent = '分析中...';
    const text = document.getElementById('tender-text').value;
    if (!text.trim()) {
      renderResult(tenderResult, '请输入文本');
      return;
    }
    try {
      const payload = { text, async_mode: false };
      const data = await authFetch('/api/bidding/analyze/text', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      renderResult(tenderResult, data);
    } catch (error) {
      console.error(error);
      renderResult(tenderResult, error.message || '分析失败');
    }
  });

  fileForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const fileInput = document.getElementById('tender-file');
    if (!fileInput.files || fileInput.files.length === 0) {
      renderResult(tenderResult, '请先选择文件');
      return;
    }
    tenderResult.textContent = '上传并分析中...';
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    try {
      const data = await authFetch('/api/bidding/analyze/file', {
        method: 'POST',
        body: formData,
      });
      renderResult(tenderResult, data);
    } catch (error) {
      console.error(error);
      renderResult(tenderResult, error.message || '分析失败');
    }
  });
}

function bindWorkloadForm() {
  const form = document.getElementById('workload-form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    workloadResult.textContent = '分析中...';
    const file = document.getElementById('workload-file').files?.[0];
    if (!file) {
      renderResult(workloadResult, '请上传 Excel 文件');
      return;
    }
    const payload = {
      config: {
        strategy: document.getElementById('workload-strategy').value,
      },
    };
    const limit = document.getElementById('workload-limit').value;
    if (limit) {
      payload.config.total_limit = Number(limit);
    }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(payload));
    try {
      const data = await authFetch('/api/workload/analyze', {
        method: 'POST',
        body: formData,
      });
      renderResult(workloadResult, data);
    } catch (error) {
      console.error(error);
      renderResult(workloadResult, error.message || '拆分失败');
    }
  });
}

function bindCostingForm() {
  const form = document.getElementById('costing-form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    costingResult.textContent = '计算中...';
    const file = document.getElementById('costing-file').files?.[0];
    if (!file) {
      renderResult(costingResult, '请上传 Excel 文件');
      return;
    }
    const rates = collectRates();
    const ratios = collectRatios();
    const payload = {
      config: {
        rates,
        architect_ratio: ratios.architect_ratio,
        project_manager_ratio: ratios.project_manager_ratio,
      },
    };
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(payload));
    try {
      const data = await authFetch('/api/costing/analyze', {
        method: 'POST',
        body: formData,
      });
      renderResult(costingResult, data);
    } catch (error) {
      console.error(error);
      renderResult(costingResult, error.message || '计算失败');
    }
  });
}

function bindLogout() {
  logoutBtn?.addEventListener('click', () => {
    clearToken();
    showAuth();
  });
}

function init() {
  fillDefaultRates();
  bindAuthForms();
  bindTenderForms();
  bindWorkloadForm();
  bindCostingForm();
  bindLogout();
  initTabs();

  const token = readToken();
  if (token) {
    fetchProfile();
  } else {
    showAuth();
  }
}

document.addEventListener('DOMContentLoaded', init);
