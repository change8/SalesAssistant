const { request, setToken } = require('../../utils/request');

Page({
  data: {
    phone: '',
    password: '',
    loading: false
  },
  onShow() {
    wx.setNavigationBarTitle({ title: '账号登录' });
  },
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value.trim() });
  },
  onPasswordInput(e) {
    this.setData({ password: e.detail.value });
  },
  async onLogin() {
    const { phone, password } = this.data;
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '请输入有效手机号', icon: 'none' });
      return;
    }
    if (!password) {
      wx.showToast({ title: '请输入密码', icon: 'none' });
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
      wx.redirectTo({ url: '/pages/home/home' });
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  }
});
