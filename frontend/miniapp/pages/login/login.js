const { request, setToken, getToken } = require('../../utils/request');

Page({
  data: {
    phone: '',
    password: '',
    loading: false
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
        wx.switchTab({ url: '/pages/tools/tools' });
      }, 500);
    } catch (error) {
      console.error('Login failed:', error);
      wx.showToast({ title: error.message || '登录失败', icon: 'none', duration: 2000 });
    } finally {
      this.setData({ loading: false });
    }
  },
  onGoRegister() {
    wx.navigateTo({ url: '/pages/register/register' });
  }
});
