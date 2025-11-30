const app = getApp();

Page({
  data: {
    userInfo: {
      name: '用户'
    }
  },

  onShow() {
    this.updateUserInfo();
    wx.setNavigationBarTitle({ title: '销售助手' });
  },

  updateUserInfo() {
    const userInfo = wx.getStorageSync('sa_user');
    if (userInfo) {
      this.setData({
        userInfo: {
          name: userInfo.username || '用户'
        }
      });
    }
  },

  navigateToSearch(e) {
    const tab = e.currentTarget.dataset.tab;
    // Switch to search tab and pass parameter (Mini Program tab switch doesn't support params directly, 
    // so we use globalData or storage to pass the active tab)
    app.globalData.activeSearchTab = tab;
    wx.switchTab({
      url: '/pages/search/search'
    });
  }
});
