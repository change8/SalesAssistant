const app = getApp();

Page({
  data: {
    userInfo: {
      name: '用户'
    },
    searchHistory: []
  },

  onShow() {
    this.updateUserInfo();
    this.updateGreeting();
    this.fetchSearchHistory();
  },

  async fetchSearchHistory() {
    try {
      const { request } = require('../../utils/request.js');
      const res = await request({
        url: '/search/history',
        method: 'GET',
        data: { limit: 10 }
      });

      // Map tab index/name for display
      const typeMap = {
        'contract': { label: '合同', icon: '📝' },
        'qualification': { label: '资质', icon: '🏆' },
        'intellectual_property': { label: '知产', icon: '💼' },
        'employee': { label: '人员', icon: '👥' },
        'company': { label: '公司', icon: '🏢' },
        'company_detail': { label: '公司详情', icon: '🏢' }
      };

      const history = (res || []).map(item => {
        const filters = item.filters || {};
        let tab = 'contracts';
        let displayType = '搜索';
        let icon = '🔍';

        // 1. Use backend "type" if available (most reliable)
        if (filters.type) {
          if (typeMap[filters.type]) {
            displayType = typeMap[filters.type].label;
            icon = typeMap[filters.type].icon;
            if (filters.type === 'company') tab = 'company';
            if (filters.type === 'contract') tab = 'contracts';
            if (filters.type === 'qualification') tab = 'qualifications';
            if (filters.type === 'intellectual_property') tab = 'ip';
            if (filters.type === 'employee') tab = 'personnel';
          }
        } else {
          // Fallback Logic (Legacy records)
          if (filters.customer || filters.contract_type || filters.project_code || filters.is_fp) {
            displayType = '合同'; icon = '📝'; tab = 'contracts';
          } else if (filters.category === 'qualification' || filters.qualification_type) {
            displayType = '资质'; icon = '🏆'; tab = 'qualifications';
          } else if (filters.category === 'intellectual_property' || filters.business_type) {
            displayType = '知产'; icon = '💼'; tab = 'ip';
          } else if (filters.certificate_name || filters.degree || filters.status) { // Employee params
            // Note: 'status' is ambiguous (Contract or Emp), but usually contract has other fields.
            displayType = '人员'; icon = '👥'; tab = 'personnel';
          } else if (filters.operating_state) {
            displayType = '公司'; icon = '🏢'; tab = 'company';
          }
        }

        // Format time
        const time = new Date(item.search_time).toLocaleDateString();

        return {
          ...item,
          displayType,
          icon,
          tab,
          time,
          tags: this.formatFilterTags(filters)
        };
      });

      this.setData({ searchHistory: history });
    } catch (err) {
      console.error('Fetch history failed', err);
    }
  },

  formatFilterTags(filters) {
    const tags = [];
    // Contracts
    if (filters.is_fp === true || filters.is_fp === 'true') tags.push('只看FP');
    if (filters.customer) tags.push(`客户:${filters.customer}`);
    if (filters.contract_type) tags.push(filters.contract_type);
    if (filters.contract_amount) tags.push(filters.contract_amount); // Corrected from undefined variable if any

    // Qualifications / IP
    if (filters.qualification_type) tags.push(filters.qualification_type);
    if (filters.business_type) tags.push(filters.business_type);
    if (filters.is_expired === false || filters.is_expired === 'false') tags.push('未过期');

    // Company
    if (filters.company) tags.push(filters.company);
    if (filters.operating_state) tags.push(filters.operating_state);

    // Employees
    if (filters.name) tags.push(filters.name);
    if (filters.degree) tags.push(filters.degree);
    if (filters.certificate_name) tags.push(filters.certificate_name);

    return tags.slice(0, 3); // Show max 3 tags
  },

  onHistoryTap(e) {
    const item = e.currentTarget.dataset.item;
    // Store history item in global data to be picked up by search page
    app.globalData.activeSearchTab = item.tab;
    app.globalData.searchHistoryAction = {
      query: item.query,
      filters: item.filters
    };
    wx.switchTab({
      url: '/pages/search/search'
    });
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
