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
