const app = getApp();

Page({
  data: {
    userInfo: {
      name: '用户'
    }
  },

  onShow() {
    this.updateUserInfo();
    this.updateGreeting();
  },

  updateUserInfo() {
    const userInfo = wx.getStorageSync('sa_user');
    if (userInfo) {
      this.setData({
        userInfo: {
          name: userInfo.full_name || userInfo.username || '用户'
        }
      });
    }
  },

  updateGreeting() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const dayMap = ['日', '一', '二', '三', '四', '五', '六'];
    const dy = dayMap[now.getDay()];

    // Countdown to next Jan 1st
    const nextYear = year + 1;
    const nextJan1 = new Date(nextYear, 0, 1);
    const diffTime = Math.abs(nextJan1 - now);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    this.setData({
      greeting: {
        dateStr: `${year} 年 ${month} 月 ${date} 日`,
        weekDay: `星期${dy}`,
        nextYearShort: nextYear % 100,
        daysLeft: diffDays
      }
    });
  },

  navigateToSearch(e) {
    const tab = e.currentTarget.dataset.tab;
    app.globalData.activeSearchTab = tab;
    wx.switchTab({
      url: '/pages/search/search'
    });
  }
});
