const { request, setToken, getToken } = require('../../utils/request');

Page({
  data: {
    phone: '',
    password: '',
    loading: false,
    isPasswordVisible: false
  },

  togglePasswordVisibility() {
    this.setData({
      isPasswordVisible: !this.data.isPasswordVisible
    });
  },
  onLoad() {
    const sysInfo = wx.getSystemInfoSync();
    this.setData({
      statusBarHeight: sysInfo.statusBarHeight
    });
  },
  onShow() {
    wx.setNavigationBarTitle({ title: '账号登录' });
    const token = getToken();
    if (token) {
      wx.switchTab({ url: '/pages/tools/tools' });
    }
  },
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value });
  },
  onPasswordInput(e) {
    this.setData({ password: e.detail.value });
  },
  async onLogin() {
    const { phone, password } = this.data;

    if (!phone || !password) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    try {
      const data = await request({
        url: '/auth/login',
        method: 'POST',
        data: { phone, password }
      });

      setToken(data.access_token);
      wx.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => {
        wx.switchTab({ url: '/pages/home/home' });
      }, 500);
    } catch (error) {
      console.error('Login failed:', error);
      // Handle both Error objects and Response objects (from request.js reject)
      let msg = '登录失败';
      if (error && error.data && error.data.detail) {
        msg = error.data.detail;
      } else if (error && error.message) {
        msg = error.message;
      } else if (error && error.errMsg) {
        msg = error.errMsg;
      }
      wx.showToast({ title: msg, icon: 'none', duration: 2000 });
    } finally {
      this.setData({ loading: false });
    }
  },
  onGoRegister() {
    wx.navigateTo({ url: '/pages/register/register' });
  },

  async onGetPhoneNumber(e) {
    if (!e.detail.code) {
      wx.showToast({ title: '获取手机号失败', icon: 'none' });
      return;
    }

    const phoneCode = e.detail.code;
    this.setData({ loading: true });

    try {
      // 1. Get Login Code
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        });
      });

      if (!loginRes.code) {
        throw new Error('微信登录失败');
      }

      // 2. Call Backend API
      const data = await request({
        url: '/auth/wechat-login',
        method: 'POST',
        data: {
          login_code: loginRes.code,
          phone_code: phoneCode
        }
      });

      // 3. Handle Success
      setToken(data.access_token);
      wx.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => {
        wx.switchTab({ url: '/pages/home/home' });
      }, 500);

    } catch (error) {
      console.error('WeChat Login failed:', error);
      const errorMessage = error.message || '登录失败';
      if (errorMessage.length > 20) {
        wx.showModal({
          title: '提示',
          content: errorMessage,
          showCancel: false,
          confirmText: '知道了'
        });
      } else {
        wx.showToast({ title: errorMessage, icon: 'none' });
      }
    } finally {
      this.setData({ loading: false });
    }
  }
});
