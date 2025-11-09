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
    console.log('getRealtimePhoneNumber event:', e);

    // 新版API的事件名称
    if (e.detail.errMsg !== 'getRealtimePhoneNumber:ok') {
      const err = e.detail.errMsg || '需要手机号授权';
      console.error('Phone auth failed:', err);
      wx.showToast({ title: err, icon: 'none', duration: 2000 });
      return;
    }

    // 新版API返回code，不是encryptedData
    const { code } = e.detail;
    if (!code) {
      wx.showToast({ title: '授权数据缺失，请重试', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    try {
      // 获取微信登录code
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

      // 发送到后端（新版API参数）
      const data = await request({
        url: '/auth/wechat-login',
        method: 'POST',
        data: {
          login_code: loginRes.code,  // 微信登录code
          phone_code: code             // 手机号code（新版）
        }
      });

      setToken(data.access_token);
      wx.showToast({ title: '登录成功', icon: 'success' });

      setTimeout(() => {
        wx.switchTab({ url: '/pages/tools/tools' });
      }, 1000);

    } catch (error) {
      console.error('wechat login error', error);
      const msg = error.message || error.errMsg || '登录失败，请稍后重试';
      wx.showToast({ title: msg, icon: 'none', duration: 2000 });
    } finally {
      this.setData({ loading: false });
    }
  }
});
