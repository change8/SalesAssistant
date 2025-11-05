const { request, setToken, getToken } = require('../../utils/request');

Page({
  data: {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    loading: false
  },
  onShow() {
    if (!getToken()) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    wx.setNavigationBarTitle({ title: '修改密码' });
  },
  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: e.detail.value });
  },
  async onSubmit() {
    const { currentPassword, newPassword, confirmPassword } = this.data;
    if (!currentPassword) {
      wx.showToast({ title: '请输入当前密码', icon: 'none' });
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      wx.showToast({ title: '新密码至少 8 位', icon: 'none' });
      return;
    }
    if (!/[A-Za-z]/.test(newPassword) || !/[0-9]/.test(newPassword)) {
      wx.showToast({ title: '新密码需包含字母和数字', icon: 'none' });
      return;
    }
    if (newPassword !== confirmPassword) {
      wx.showToast({ title: '两次输入的密码不一致', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    try {
      const data = await request({
        url: '/auth/change-password',
        method: 'POST',
        data: {
          current_password: currentPassword,
          new_password: newPassword
        }
      });
      setToken(data.access_token);
      wx.showToast({ title: '密码已更新', icon: 'success' });
      setTimeout(() => {
        wx.navigateBack();
      }, 400);
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  }
});
