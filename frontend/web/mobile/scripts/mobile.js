// Mobile API Client and Utilities

const API_BASE = '/api';
const TOKEN_KEY = 'sa_token';

// ===== Storage Utilities =====
const storage = {
    get(key) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch {
            return localStorage.getItem(key);
        }
    },

    set(key, value) {
        const data = typeof value === 'string' ? value : JSON.stringify(value);
        localStorage.setItem(key, data);
    },

    remove(key) {
        localStorage.removeItem(key);
    },

    clear() {
        localStorage.clear();
    }
};

// ===== Auth Utilities =====
const auth = {
    getToken() {
        return storage.get(TOKEN_KEY);
    },

    setToken(token) {
        storage.set(TOKEN_KEY, token);
    },

    removeToken() {
        storage.remove(TOKEN_KEY);
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    logout() {
        this.removeToken();
        storage.remove('sa_user_role');
        storage.remove('sa_user_name');
        window.location.href = 'login.html';
    }
};

// ===== API Client =====
async function apiCall(endpoint, method = 'GET', body = null) {
    const token = auth.getToken();
    const headers = {};

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers
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

        // Handle 401 Unauthorized
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
            showToast('登录已过期，请重新登录', 'error');
            auth.logout();
            return new Promise(() => { });
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

// ===== UI Utilities =====
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
    position: fixed;
    top: 70px;
    left: 50%;
    transform: translateX(-50%);
    background: ${type === 'error' ? '#FF4757' : type === 'success' ? '#26DE81' : '#3366FF'};
    color: white;
    padding: 12px 24px;
    border-radius: 24px;
    font-size: 14px;
    z-index: 10000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideDown 0.3s ease;
  `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showLoading(container) {
    container.innerHTML = `
    <div class="loading">
      <div class="loading-spinner"></div>
      <div>加载中...</div>
    </div>
  `;
}

function showEmpty(container, message = '暂无数据') {
    container.innerHTML = `
    <div class="empty-state">
      <div class="icon">📭</div>
      <div class="message">${message}</div>
    </div>
  `;
}

function showError(container, message = '加载失败') {
    container.innerHTML = `
    <div class="empty-state">
      <div class="icon">⚠️</div>
      <div class="message">${message}</div>
      <button class="btn btn-primary btn-sm mt-16" onclick="location.reload()">重试</button>
    </div>
  `;
}

// ===== Touch Utilities =====
class TouchHandler {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            threshold: options.threshold || 50,
            onSwipeLeft: options.onSwipeLeft,
            onSwipeRight: options.onSwipeRight,
            onSwipeUp: options.onSwipeUp,
            onSwipeDown: options.onSwipeDown,
            onPullDown: options.onPullDown
        };

        this.startX = 0;
        this.startY = 0;
        this.startTime = 0;

        this.init();
    }

    init() {
        this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        this.element.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }

    handleTouchStart(e) {
        this.startX = e.touches[0].clientX;
        this.startY = e.touches[0].clientY;
        this.startTime = Date.now();
    }

    handleTouchEnd(e) {
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        const endTime = Date.now();

        const deltaX = endX - this.startX;
        const deltaY = endY - this.startY;
        const deltaTime = endTime - this.startTime;

        // Ignore if too slow
        if (deltaTime > 500) return;

        // Horizontal swipe
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > this.options.threshold) {
            if (deltaX > 0 && this.options.onSwipeRight) {
                this.options.onSwipeRight();
            } else if (deltaX < 0 && this.options.onSwipeLeft) {
                this.options.onSwipeLeft();
            }
        }

        // Vertical swipe
        if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > this.options.threshold) {
            if (deltaY > 0 && this.options.onSwipeDown) {
                this.options.onSwipeDown();
            } else if (deltaY < 0 && this.options.onSwipeUp) {
                this.options.onSwipeUp();
            }
        }
    }
}

// ===== Pull to Refresh =====
function initPullToRefresh(container, onRefresh) {
    let startY = 0;
    let isPulling = false;

    container.addEventListener('touchstart', (e) => {
        if (container.scrollTop === 0) {
            startY = e.touches[0].clientY;
            isPulling = true;
        }
    }, { passive: true });

    container.addEventListener('touchmove', (e) => {
        if (!isPulling) return;

        const currentY = e.touches[0].clientY;
        const diff = currentY - startY;

        if (diff > 60) {
            // Show refresh indicator
            const indicator = document.querySelector('.pull-to-refresh');
            if (indicator) {
                indicator.classList.add('active');
            }
        }
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
        if (!isPulling) return;

        const endY = e.changedTouches[0].clientY;
        const diff = endY - startY;

        if (diff > 60 && onRefresh) {
            onRefresh();
        }

        // Hide refresh indicator
        const indicator = document.querySelector('.pull-to-refresh');
        if (indicator) {
            indicator.classList.remove('active');
        }

        isPulling = false;
    }, { passive: true });
}

// ===== Format Utilities =====
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function formatAmount(amount) {
    if (!amount && amount !== 0) return '-';
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY'
    }).format(amount);
}

function truncate(text, length = 50) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

// ===== Debounce =====
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ===== Check Auth on Page Load =====
function checkAuth(requireAuth = true) {
    const isAuthPage = window.location.pathname.includes('login.html') ||
        window.location.pathname.includes('register.html');

    if (requireAuth && !auth.isAuthenticated() && !isAuthPage) {
        window.location.href = 'login.html';
    } else if (!requireAuth && auth.isAuthenticated() && isAuthPage) {
        window.location.href = 'index.html';
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }
  
  @keyframes slideUp {
    from {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
    to {
      opacity: 0;
      transform: translateX(-50%) translateY(-20px);
    }
  }
`;
document.head.appendChild(style);
