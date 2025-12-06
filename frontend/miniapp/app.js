App({
  globalData: {
    token: '',
    apiBase: '',
    userInfo: null
  },
  async onLaunch() {
    try {
      const config = require('./config.js');
      this.globalData.apiBase = config.apiBaseUrl.replace(/\/$/, '');
    } catch (error) {
      console.error('Missing config.js. Please create frontend/miniapp/config.js with apiBaseUrl.');
    }

    const { request, setToken } = require('./utils/request');

    // 1. Check if we have a stored token
    const storedToken = wx.getStorageSync('sa_token');
    const storedUser = wx.getStorageSync('sa_user');

    if (storedToken && storedUser) {
      this.globalData.token = storedToken;
      this.globalData.userInfo = storedUser;

      // Auto-jump to Home
      wx.switchTab({ url: '/pages/home/home' });
      return;
    }

    // 2. Silent Login (using wx.login code only)
    try {
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        });
      });

      if (loginRes.code) {
        // Attempt silent login without phone code
        const data = await request({
          url: '/auth/wechat-login',
          method: 'POST',
          data: {
            login_code: loginRes.code
            // phone_code omitted
          },
          // Suppress global error toast for silent login
          header: { 'X-Silent-Error': 'true' }
        }).catch(() => null); // Catch error to proceed to manual login

        if (data && data.access_token) {
          // Silent Login Success!
          setToken(data.access_token);

          // Fetch user info
          const userInfo = await request({ url: '/auth/me' });
          wx.setStorageSync('sa_user', userInfo);
          this.globalData.userInfo = userInfo;

          wx.switchTab({ url: '/pages/home/home' });
          return;
        }
      }
    } catch (e) {
      console.log('Silent login failed:', e);
    }

    // 3. Fallback to Manual Login
    // If not on a tabbar page, we might need to redirect.
    // Since app.json likely sets 'pages/login/login' as first page, or home?
    // If home is first page, we need to redirect to login if silent login fails.
    // Let's assume Login is NOT the entry page in app.json for this flow to work cleanly, 
    // OR we reLaunch to Home if success, else reLaunch to Login.

    // Check current page? No, onLaunch is too early.
    // Just ensure we end up at Login if we didn't switchTab to Home.
    wx.reLaunch({ url: '/pages/login/login' });
  }
});
