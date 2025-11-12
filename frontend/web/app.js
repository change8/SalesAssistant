const API_BASE = '/api';
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

const PHONE_PATTERN = /^1[3-9]\d{9}$/;
const PRIORITY_LABELS = {
  critical: '极高优先级',
  high: '高优先级',
  medium: '中优先级',
  low: '关注即可',
};

const workloadResult = document.getElementById('workload-result');
const costingResult = document.getElementById('costing-result');
const taskListEl = document.getElementById('task-list');
const taskDetailEl = document.getElementById('task-detail');
const taskFilterEl = document.getElementById('task-filter');
const taskRefreshBtn = document.getElementById('task-refresh-btn');
const taskToggleHistoryBtn = document.getElementById('task-toggle-history');

let taskViewMode = 'active';
let taskPollingTimer = null;
let currentTaskFilter = 'all';
let selectedTaskId = null;
let cachedTasks = [];

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

function showApp(user) {
  authSection.classList.add('hidden');
  appSection.classList.remove('hidden');
  userInfoEl.textContent = `欢迎，${user.full_name || user.phone}`;
}

function showAuth() {
  appSection.classList.add('hidden');
  authSection.classList.remove('hidden');
  userInfoEl.textContent = '';
  stopTaskPolling();
  if (taskListEl) taskListEl.innerHTML = '';
  renderTaskDetail(null);
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

function setActiveTab(targetId) {
  document.querySelectorAll('.tab-panel').forEach((panel) => {
    panel.classList.toggle('hidden', panel.id !== targetId);
  });
  if (targetId === 'tasks-tab') {
    startTaskPolling();
  } else {
    stopTaskPolling();
    selectedTaskId = null;
    renderTaskDetail(null);
  }
}

function initTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      if (btn.classList.contains('active')) return;
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      setActiveTab(btn.dataset.target);
    });
  });

  const activeButton = document.querySelector('.tab-btn.active');
  const initialTarget = activeButton ? activeButton.dataset.target : 'tender-tab';
  setActiveTab(initialTarget);
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

function formatTaskType(type) {
  switch (type) {
    case 'bidding_analysis':
      return '标书分析';
    case 'workload_analysis':
      return '工时拆分';
    case 'costing_estimate':
      return '成本预估';
    default:
      return type || '任务';
  }
}

function formatTaskStatus(status) {
  switch (status) {
    case 'pending':
      return '排队中';
    case 'running':
      return '处理中';
    case 'succeeded':
      return '已完成';
    case 'failed':
      return '失败';
    default:
      return status || '未知';
  }
}

function formatDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return String(value);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

function renderTaskList(tasks = []) {
  if (!taskListEl) return;
  cachedTasks = tasks;
  taskListEl.innerHTML = '';
  if (!tasks.length) {
    renderTaskDetail(null);
    const empty = document.createElement('div');
    empty.className = 'task-item';
    empty.innerHTML = '<span class=\"muted\">暂无任务，提交分析后这里会显示进度。</span>';
    taskListEl.appendChild(empty);
    return;
  }

  tasks.forEach((task) => {
    const item = document.createElement('div');
    item.className = `task-item${task.id === selectedTaskId ? ' active' : ''}`;
    item.dataset.taskId = task.id;

    const title = document.createElement('div');
    title.className = 'task-title';
    title.textContent = `${formatTaskType(task.task_type)} · #${task.id}`;
    item.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'task-meta';
    const status = document.createElement('span');
    status.className = `task-status ${task.status}`;
    status.textContent = formatTaskStatus(task.status);
    meta.appendChild(status);

    if (task.created_at) {
      const created = document.createElement('span');
      created.textContent = `创建 ${formatDateTime(task.created_at)}`;
      meta.appendChild(created);
    }
    if (task.finished_at) {
      const finished = document.createElement('span');
      finished.textContent = `完成 ${formatDateTime(task.finished_at)}`;
      meta.appendChild(finished);
    }
    if (task.error_message && task.status === 'failed') {
      const err = document.createElement('span');
      err.textContent = task.error_message.slice(0, 80);
      meta.appendChild(err);
    }
    item.appendChild(meta);

    item.addEventListener('click', () => {
      selectTask(task.id);
    });

    taskListEl.appendChild(item);
  });
}

function renderTaskDetail(task) {
  if (!taskDetailEl) return;
  if (!task) {
    taskDetailEl.innerHTML = '<p class=\"muted\">选择任务以查看详情</p>';
    return;
  }
  const statusLabel = formatTaskStatus(task.status);
  const detailParts = [];
  detailParts.push(`<h3>${formatTaskType(task.task_type)} · #${task.id}</h3>`);
  detailParts.push(
    `<p class=\"task-meta\">状态 <span class=\"task-status ${task.status}\">${statusLabel}</span> · 创建 ${formatDateTime(
      task.created_at,
    )}${task.finished_at ? ` · 完成 ${formatDateTime(task.finished_at)}` : ''}</p>`,
  );
  if (task.error_message) {
    detailParts.push(`<p class=\"task-meta\" style=\"color:#c42828;\">${task.error_message}</p>`);
  }
  if (task.result_payload) {
    const pretty = JSON.stringify(task.result_payload, null, 2);
    detailParts.push(`<pre>${pretty}</pre>`);
  } else if (task.status === 'failed') {
    detailParts.push('<p class=\"muted\">任务失败，未生成可用结果。</p>');
  } else {
    detailParts.push('<p class=\"muted\">任务仍在处理中，稍后再试。</p>');
  }
  taskDetailEl.innerHTML = detailParts.join('');
}

async function selectTask(taskId) {
  selectedTaskId = taskId;
  renderTaskList(cachedTasks);
  try {
    const task = await authFetch(`/api/tasks/${taskId}`);
    renderTaskDetail(task);
  } catch (error) {
    console.error('加载任务详情失败', error);
    renderTaskDetail(null);
  }
}

async function loadTasks(options = {}) {
  const { silent = false } = options;
  if (!taskListEl) return;
  try {
    const params = new URLSearchParams();
    params.set('limit', taskViewMode === 'history' ? 50 : 20);
    if (currentTaskFilter && currentTaskFilter !== 'all') {
      params.set('task_type', currentTaskFilter);
    }
    const endpoint = taskViewMode === 'history' ? `/api/tasks/history?${params}` : `/api/tasks?${params}`;
    const data = await authFetch(endpoint);
    const items = Array.isArray(data?.items) ? data.items : [];
    renderTaskList(items);
    if (selectedTaskId && !items.some((item) => item.id === selectedTaskId)) {
      if (taskViewMode === 'active') {
        selectedTaskId = null;
        renderTaskDetail(null);
      }
    }
  } catch (error) {
    if (!silent) console.error('加载任务列表失败', error);
  }
}

function stopTaskPolling() {
  if (taskPollingTimer) {
    clearInterval(taskPollingTimer);
    taskPollingTimer = null;
  }
}

function startTaskPolling() {
  if (!taskListEl) return;
  stopTaskPolling();
  loadTasks();
  if (taskViewMode === 'active') {
    taskPollingTimer = setInterval(() => loadTasks({ silent: true }), 5000);
  }
}

function showTaskCreatedMessage(target, task) {
  if (!target || !task) return;
  target.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'task-created';
  const taskLabel = `${formatTaskType(task.task_type || '')} · #${task.id}`;
  wrapper.innerHTML = `<strong>任务已创建</strong><span>${taskLabel} 已进入队列，可在“任务中心”查看进度。</span>`;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'link-btn';
  button.textContent = '打开任务中心';
  button.addEventListener('click', () => {
    const tasksBtn = document.querySelector('.tab-btn[data-target=\"tasks-tab\"]');
    if (tasksBtn) {
      tasksBtn.click();
    }
    if (taskViewMode === 'history') {
      taskViewMode = 'active';
      if (taskToggleHistoryBtn) {
        taskToggleHistoryBtn.dataset.mode = 'history';
        taskToggleHistoryBtn.textContent = '查看历史任务';
      }
    }
    selectedTaskId = task.id;
    setTimeout(() => {
      selectTask(task.id);
    }, 200);
  });
  wrapper.appendChild(button);
  target.appendChild(wrapper);
}

function bindAuthForms() {
  const loginForm = document.getElementById('login-form');

  loginForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const phoneInput = document.getElementById('login-phone');
    const pwdInput = document.getElementById('login-password');
    const phone = phoneInput?.value.trim() || '';
    const password = pwdInput?.value || '';

    if (!PHONE_PATTERN.test(phone)) {
      setAuthMessage('请输入 11 位有效手机号', 'error');
      phoneInput?.focus();
      return;
    }
    if (password.length === 0) {
      setAuthMessage('请输入密码', 'error');
      pwdInput?.focus();
      return;
    }
    if (password.length > 64) {
      setAuthMessage('密码长度不能超过 64 位', 'error');
      pwdInput?.focus();
      return;
    }

    setAuthMessage('登录中...', 'info');
    const payload = { phone, password };
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
}

function bindWorkloadForm() {
  const form = document.getElementById('workload-form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    workloadResult.textContent = '任务创建中...';
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
      const task = await authFetch('/api/workload/analyze', {
        method: 'POST',
        body: formData,
      });
      showTaskCreatedMessage(workloadResult, task);
      if (task && task.id) {
        selectedTaskId = task.id;
      }
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
    costingResult.textContent = '任务创建中...';
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
      const task = await authFetch('/api/costing/analyze', {
        method: 'POST',
        body: formData,
      });
      showTaskCreatedMessage(costingResult, task);
      if (task && task.id) {
        selectedTaskId = task.id;
      }
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

function bindTaskControls() {
  taskFilterEl?.addEventListener('change', () => {
    currentTaskFilter = taskFilterEl.value || 'all';
    loadTasks();
  });

  taskRefreshBtn?.addEventListener('click', () => {
    loadTasks();
  });

  taskToggleHistoryBtn?.addEventListener('click', () => {
    if (taskViewMode === 'active') {
      taskViewMode = 'history';
      taskToggleHistoryBtn.textContent = '返回进行中';
      taskToggleHistoryBtn.dataset.mode = 'active';
    } else {
      taskViewMode = 'active';
      taskToggleHistoryBtn.textContent = '查看历史任务';
      taskToggleHistoryBtn.dataset.mode = 'history';
    }
    if (document.getElementById('tasks-tab')?.classList.contains('hidden')) {
      stopTaskPolling();
      loadTasks();
    } else {
      startTaskPolling();
    }
  });
}

function init() {
  fillDefaultRates();
  bindAuthForms();
  bindWorkloadForm();
  bindCostingForm();
  bindLogout();
  bindTaskControls();
  initTabs();

  const token = readToken();
  if (token) {
    fetchProfile();
  } else {
    showAuth();
  }
}

document.addEventListener('DOMContentLoaded', init);
