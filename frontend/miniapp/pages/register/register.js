const { request } = require('../../utils/request');

Page({
  data: {
    phone: '',
    username: '',
    password: '',
    confirmPassword: '',
    loading: false
  },
  onShow() {
    wx.setNavigationBarTitle({ title: '账号注册' });
  },
  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: e.detail.value.trim() });
  },
  async onSubmit() {
    const { phone, username, password, confirmPassword } = this.data;
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '请输入有效手机号', icon: 'none' });
      return;
    }
    if (!username) {
      wx.showToast({ title: '请输入用户名', icon: 'none' });
      return;
    }
    if (!password || password.length < 8) {
      wx.showToast({ title: '密码至少 8 位', icon: 'none' });
      return;
    }
    if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
      wx.showToast({ title: '密码需包含字母和数字', icon: 'none' });
      return;
    }
    if (password !== confirmPassword) {
      wx.showToast({ title: '两次输入的密码不一致', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    try {
      await request({
        url: '/auth/register',
        method: 'POST',
        data: {
          phone,
          full_name: username,
          password
        }
      });
      wx.showToast({ title: '注册成功', icon: 'success' });
      setTimeout(() => {
        wx.navigateBack();
      }, 500);
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  },
  onGoLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  }
});
