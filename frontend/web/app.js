const API_BASE = '/api';
const TOKEN_KEY = 'sa_token';

// --- Auth Helpers ---

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function checkAuth() {
  const token = getToken();
  const isAuthPage = window.location.pathname.includes('login.html') || window.location.pathname.includes('register.html');

  if (!token && !isAuthPage) {
    window.location.href = 'login.html';
  } else if (token && isAuthPage) {
    window.location.href = 'index.html';
  }
}

function logout() {
  removeToken();
  window.location.href = 'login.html';
}

// --- Bidding Logic ---

function handleBiddingUpload(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];

    // Show loading state (optional, can be improved)
    const uploadArea = document.getElementById('biddingUpload');
    const originalContent = uploadArea.innerHTML;
    uploadArea.innerHTML = '<h3 class="text-h3">正在分析标书...</h3><p class="text-sm">AI 正在提取关键信息，请稍候</p>';

    // Simulate API call delay
    setTimeout(() => {
      // TODO: Replace with actual API call
      // const formData = new FormData();
      // formData.append('file', file);
      // apiCall('/bidding/analyze', 'POST', formData).then(data => renderBiddingResult(data));

      // Mock Data for Demo
      const mockData = {
        totalScore: 90,
        businessScore: 40,
        techScore: 50,
        disqualifiers: [
          "等保三级证书：不满足（需提供原件扫描件）",
          "近三年无重大违法记录声明：缺失"
        ],
        timeline: [
          { date: "2025-11-20", event: "标书购买截止" },
          { date: "2025-11-24", event: "投标保证金缴纳 (3000元)" },
          { date: "2025-11-28", event: "投标截止 / 开标" }
        ],
        suggestions: [
          "运营要求超过 1 年，需确认团队稳定性",
          "无首付款，需评估资金占用成本",
          "需现场述标，提前安排差旅"
        ]
      };

      renderBiddingResult(mockData);

      // Reset upload area for next time
      uploadArea.innerHTML = originalContent;
      input.value = ''; // Clear input
    }, 2000);
  }
}

function renderBiddingResult(data) {
  // Switch Views
  document.getElementById('bidding-upload-state').style.display = 'none';
  document.getElementById('bidding-result-state').style.display = 'block';

  // Fill Data
  document.getElementById('totalScore').textContent = data.totalScore;
  document.getElementById('businessScore').textContent = data.businessScore;
  document.getElementById('techScore').textContent = data.techScore;

  // Disqualifiers
  const dqList = document.getElementById('disqualifierList');
  dqList.innerHTML = data.disqualifiers.map(item => `<li>${item}</li>`).join('');

  // Timeline
  const tlList = document.getElementById('timelineList');
  tlList.innerHTML = data.timeline.map(item => `
        <div class="timeline-item">
            <div class="timeline-date">${item.date}</div>
            <div class="text-body">${item.event}</div>
        </div>
    `).join('');

  // Suggestions
  const sgList = document.getElementById('suggestionList');
  sgList.innerHTML = data.suggestions.map(item => `<li>${item}</li>`).join('');
}

function resetBidding() {
  document.getElementById('bidding-result-state').style.display = 'none';
  document.getElementById('bidding-upload-state').style.display = 'block';
}

function toggleCollapse(id) {
  const content = document.getElementById(id);
  content.classList.toggle('open');
  // Rotate arrow logic if needed
}

function generateDoc(type) {
  alert('功能开发中：正在生成 ' + type + ' 文档...');
  // TODO: Call backend API to generate doc
}

// --- API Client ---

async function apiCall(endpoint, method = 'GET', body = null) {
  const token = getToken();
  const headers = {};

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    if (body instanceof FormData) {
      options.body = body;
    } else {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (response.status === 401) {
      logout();
      throw new Error('登录已过期，请重新登录');
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || '请求失败');
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// --- Auth Actions ---

async function login(phone, password) {
  const formData = new URLSearchParams();
  formData.append('username', phone); // FastAPI OAuth2 expects 'username'
  formData.append('password', password);

  // Note: The backend might expect JSON or Form Data depending on implementation.
  // Based on standard FastAPI OAuth2PasswordRequestForm, it expects form data.
  // However, previous app.js used JSON. Let's try JSON first as per previous code.

  try {
    // Try JSON first (custom auth endpoint)
    const data = await apiCall('/auth/login', 'POST', { phone, password });
    setToken(data.access_token);
    window.location.href = 'index.html';
  } catch (e) {
    // Fallback or error handling
    throw e;
  }
}

async function register(phone, fullName, password) {
  await apiCall('/auth/register', 'POST', {
    phone,
    full_name: fullName,
    password
  });
  // Auto login after register? Or redirect to login.
  // Let's redirect to login for simplicity
  window.location.href = 'login.html';
}
