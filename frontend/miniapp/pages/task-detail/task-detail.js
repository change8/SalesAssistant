const { request, getToken } = require('../../utils/request');

Page({
  data: {
    taskId: null,
    loading: false,
    task: null,
    resultJson: '',
    requestJson: ''
  },
  onLoad(options) {
    const { id } = options;
    this.setData({ taskId: id });
  },
  onShow() {
    if (!getToken()) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    wx.setNavigationBarTitle({ title: '任务详情' });
    this.fetchDetail();
  },
  async fetchDetail() {
    const { taskId } = this.data;
    if (!taskId) return;
    this.setData({ loading: true });
    try {
      const data = await request({ url: `/tasks/${taskId}`, method: 'GET' });
      this.setData({
        task: data,
        resultJson: data.result_payload ? JSON.stringify(data.result_payload, null, 2) : '',
        requestJson: data.request_payload ? JSON.stringify(data.request_payload, null, 2) : ''
      });
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  },
  onCopyResult() {
    if (!this.data.resultJson) return;
    wx.setClipboardData({
      data: this.data.resultJson,
      success: () => {
        wx.showToast({ title: '已复制结果', icon: 'success' });
      }
    });
  },
  onCopyRequest() {
    if (!this.data.requestJson) return;
    wx.setClipboardData({
      data: this.data.requestJson,
      success: () => {
        wx.showToast({ title: '已复制请求', icon: 'success' });
      }
    });
  }
});
