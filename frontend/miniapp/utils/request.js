const app = getApp();

function getApiBase() {
  return app?.globalData?.apiBase || '';
}

function getToken() {
  return app?.globalData?.token || '';
}

function setToken(token) {
  app.globalData.token = token;
  wx.setStorageSync('sa_token', token);
}

function clearToken() {
  app.globalData.token = '';
  wx.removeStorageSync('sa_token');
  app.globalData.userInfo = null;
  wx.removeStorageSync('sa_user');
}

function request(options) {
  const token = getToken();
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getApiBase()}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': options.contentType || 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
      timeout: options.timeout || 60000,
      success(res) {
        if (res.statusCode === 401) {
          clearToken();
          wx.showToast({ title: '登录失效，请重新登录', icon: 'none' });
          wx.redirectTo({ url: '/pages/login/login' });
          reject(res);
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const detail = res.data?.detail || res.errMsg || '请求失败';
          wx.showToast({ title: detail.toString(), icon: 'none' });
          reject(res);
        }
      },
      fail(error) {
        wx.showToast({ title: '网络错误', icon: 'none' });
        reject(error);
      }
    });
  });
}

module.exports = {
  request,
  getToken,
  setToken,
  clearToken
};
