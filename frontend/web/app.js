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

const PHONE_PATTERN = /^1[3-9]\d{9}$/;
const PRIORITY_LABELS = {
  critical: '极高优先级',
  high: '高优先级',
  medium: '中优先级',
  low: '关注即可',
};

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

function renderTenderResult(container, payload) {
  if (!container) return;
  container.innerHTML = '';

  if (typeof payload === 'string') {
    container.textContent = payload;
    return;
  }

  if (!payload || typeof payload !== 'object') {
    container.textContent = '暂无结果';
    return;
  }

  const job = payload.result ? payload : { result: payload };
  const result = job.result || {};

  const metaRow = document.createElement('div');
  metaRow.className = 'tender-meta';

  const statusText = (job.status || 'completed').toUpperCase();
  const status = document.createElement('span');
  status.className = `status-pill status-${(job.status || 'completed').toLowerCase()}`;
  status.textContent = statusText;
  metaRow.appendChild(status);

  if (job.source) {
    const source = document.createElement('span');
    source.textContent = job.source === 'file' ? '来源：文件上传' : '来源：粘贴文本';
    metaRow.appendChild(source);
  }
  if (job.filename) {
    const name = document.createElement('span');
    name.textContent = `文件：${job.filename}`;
    metaRow.appendChild(name);
  }
  if (job.text_length) {
    const length = document.createElement('span');
    length.textContent = `文本长度：${job.text_length}`;
    metaRow.appendChild(length);
  }
  container.appendChild(metaRow);

  const summaryBlock = document.createElement('div');
  summaryBlock.className = 'tender-summary';
  summaryBlock.textContent = result.summary || '模型未提供整体概述，可参考下方分类提示。';
  container.appendChild(summaryBlock);

  if (job.metadata?.raw_response === 'heuristic' || result.raw_response === 'heuristic') {
    const warning = document.createElement('div');
    warning.className = 'tender-warning';
    warning.textContent = '当前展示的是启发式结果，建议配置大模型后再次分析。';
    container.appendChild(warning);
  }

  const tabs = Array.isArray(result.tabs) ? result.tabs : [];
  if (!tabs.length) {
    const empty = document.createElement('div');
    empty.className = 'tender-empty';
    empty.textContent = '暂无分类结果，建议人工核查。';
    container.appendChild(empty);
    appendRawJson(container, payload);
    return;
  }

  tabs.forEach((tab) => {
    if (!tab || typeof tab !== 'object') return;
    const section = document.createElement('section');
    section.className = 'tender-tab';

    const header = document.createElement('header');
    header.className = 'tender-tab-header';
    const title = document.createElement('h3');
    title.textContent = tab.title || tab.id || '分类';
    header.appendChild(title);
    const count = document.createElement('span');
    count.className = 'count-pill';
    const itemsCount = Array.isArray(tab.items) ? tab.items.length : 0;
    count.textContent = itemsCount.toString();
    header.appendChild(count);
    section.appendChild(header);

    if (tab.summary) {
      const summary = document.createElement('p');
      summary.className = 'tender-tab-summary';
      summary.textContent = tab.summary;
      section.appendChild(summary);
    }

    const itemsContainer = document.createElement('div');
    itemsContainer.className = 'tender-items';
    const items = Array.isArray(tab.items) ? tab.items : [];
    if (!items.length) {
      const hint = document.createElement('div');
      hint.className = 'tender-empty';
      hint.textContent = '该分类暂无模型输出，建议人工确认。';
      itemsContainer.appendChild(hint);
    } else {
      items.forEach((item) => {
        const card = buildTenderItemCard(item);
        itemsContainer.appendChild(card);
      });
    }
    section.appendChild(itemsContainer);
    container.appendChild(section);
  });

  appendRawJson(container, payload);
}

function buildTenderItemCard(item) {
  const card = document.createElement('article');
  card.className = 'tender-item';

  const header = document.createElement('header');
  header.className = 'tender-item-header';
  const title = document.createElement('h4');
  title.textContent = firstNonEmpty(item, ['title', 'requirement', 'headline', 'name', 'event']) || '要点';
  header.appendChild(title);
  const priorityLabel = PRIORITY_LABELS[(item.priority || item.severity || '').toLowerCase()];
  if (priorityLabel) {
    const pill = document.createElement('span');
    pill.className = `priority-pill ${(item.priority || item.severity || 'medium').toLowerCase()}`;
    pill.textContent = priorityLabel;
    header.appendChild(pill);
  }
  card.appendChild(header);

  const body = document.createElement('div');
  body.className = 'tender-item-body';
  appendInfoRow(body, '为何重要', firstNonEmpty(item, ['why_important', 'reason', 'summary', 'description']));
  appendInfoRow(body, '行动建议', firstNonEmpty(item, ['guidance', 'recommendation', 'action']));
  appendInfoRow(body, '补充说明', firstNonEmpty(item, ['details', 'note', 'impact']));
  appendInfoRow(body, '原文节选', firstNonEmpty(item, ['source_excerpt', 'evidence']));
  card.appendChild(body);

  return card;
}

function appendInfoRow(container, label, value) {
  if (!value || String(value).trim() === '') return;
  const row = document.createElement('div');
  row.className = 'tender-info-row';
  const labelEl = document.createElement('span');
  labelEl.className = 'label';
  labelEl.textContent = label;
  const valueEl = document.createElement('p');
  valueEl.className = 'value';
  valueEl.textContent = value;
  row.appendChild(labelEl);
  row.appendChild(valueEl);
  container.appendChild(row);
}

function firstNonEmpty(source, keys) {
  if (!source) return '';
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return '';
}

function appendRawJson(container, data) {
  const details = document.createElement('details');
  details.className = 'raw-json-block';
  const summary = document.createElement('summary');
  summary.textContent = '查看原始 JSON';
  details.appendChild(summary);
  const pre = document.createElement('pre');
  pre.textContent = JSON.stringify(data, null, 2);
  details.appendChild(pre);
  container.appendChild(details);
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

function bindTenderForms() {
  const textForm = document.getElementById('tender-text-form');
  const fileForm = document.getElementById('tender-file-form');

  textForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    tenderResult.textContent = '分析中...';
    const text = document.getElementById('tender-text').value;
    if (!text.trim()) {
      renderTenderResult(tenderResult, '请输入文本');
      return;
    }
    try {
      const payload = { text, async_mode: false };
      const data = await authFetch('/api/bidding/analyze/text', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      renderTenderResult(tenderResult, data);
    } catch (error) {
      console.error(error);
      renderTenderResult(tenderResult, error.message || '分析失败');
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
      renderTenderResult(tenderResult, data);
    } catch (error) {
      console.error(error);
      renderTenderResult(tenderResult, error.message || '分析失败');
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
