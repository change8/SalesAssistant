const { request, setToken, getToken } = require('../../utils/request');

Page({
  data: {
    loading: false
  },
  onShow() {
    wx.setNavigationBarTitle({ title: '微信授权登录' });
    const token = getToken();
    if (token) {
      wx.switchTab({ url: '/pages/tools/tools' });
    }
  },
  async onGetPhoneNumber(e) {
    if (e.detail.errMsg !== 'getPhoneNumber:ok') {
      const err = e.detail.errMsg || '需要手机号授权';
      wx.showToast({ title: err, icon: 'none' });
      return;
    }
    const { encryptedData, iv } = e.detail;
    if (!encryptedData || !iv) {
      wx.showToast({ title: '授权数据缺失，请重试', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    try {
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          timeout: 6000,
          success: resolve,
          fail: reject
        });
      });
      if (!loginRes.code) {
        wx.showToast({ title: '微信登录失败', icon: 'none' });
        return;
      }
      const data = await request({
        url: '/auth/wechat-login',
        method: 'POST',
        data: {
          code: loginRes.code,
          encrypted_data: encryptedData,
          iv
        }
      });
      setToken(data.access_token);
      wx.showToast({ title: '登录成功', icon: 'success' });
      wx.switchTab({ url: '/pages/tools/tools' });
    } catch (error) {
      console.error('wechat login error', error);
      wx.showToast({ title: '登录失败，请稍后重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  }
});
