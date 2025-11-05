const { request, getToken, clearToken } = require('../../utils/request');

Page({
  data: {
    user: null,
    loading: false
  },
  onShow() {
    if (!getToken()) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    wx.setNavigationBarTitle({ title: '我的' });
    this.fetchProfile();
  },
  async fetchProfile() {
    this.setData({ loading: true });
    try {
      const data = await request({ url: '/auth/me', method: 'GET' });
      this.setData({ user: data });
      const app = getApp();
      app.globalData.userInfo = data;
      wx.setStorageSync('sa_user', data);
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  },
  onNavigateChangePassword() {
    wx.navigateTo({ url: '/pages/change-password/change-password' });
  },
  onNavigateAbout() {
    wx.navigateTo({ url: '/pages/about/about' });
  },
  onLogout() {
    clearToken();
    const app = getApp();
    app.globalData.userInfo = null;
    wx.removeStorageSync('sa_user');
    wx.showToast({ title: '已退出', icon: 'success' });
    setTimeout(() => {
      wx.redirectTo({ url: '/pages/login/login' });
    }, 400);
  }
});
