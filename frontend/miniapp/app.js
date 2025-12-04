App({
  globalData: {
    token: '',
    apiBase: '',
    userInfo: null
  },
  onLaunch() {
    try {
      const config = require('./config.js');
      this.globalData.apiBase = config.apiBaseUrl.replace(/\/$/, '');
    } catch (error) {
      console.error('Missing config.js. Please create frontend/miniapp/config.js with apiBaseUrl.');
    }
    const storedToken = wx.getStorageSync('sa_token');
    if (storedToken) {
      this.globalData.token = storedToken;
    } else {
      // Force login
      wx.reLaunch({
        url: '/pages/login/login'
      });
    }
    const storedUser = wx.getStorageSync('sa_user');
    if (storedUser) {
      this.globalData.userInfo = storedUser;
    }
  }
});
