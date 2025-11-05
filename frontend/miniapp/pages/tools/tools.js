const { getToken } = require('../../utils/request');

const POLL_INTERVAL = 2500;

Page({
  data: {
    activeTool: 'bidding',
    biddingUploading: false,
    biddingStatus: '',
    biddingResult: {},
    workloadUploading: false,
    workloadStatus: '',
    workloadResult: '',
    costingUploading: false,
    costingStatus: '',
    costingResult: ''
  },
  onShow() {
    if (!getToken()) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    wx.setNavigationBarTitle({ title: '工具中心' });
  },
  onSelectTool(e) {
    const { tool } = e.currentTarget.dataset;
    this.setData({ activeTool: tool });
  },
  async onPickBiddingFile() {
    try {
      const res = await wx.chooseMessageFile({ count: 1, type: 'file' });
      if (!res.tempFiles?.length) return;
      this.uploadBiddingFile(res.tempFiles[0]);
    } catch (error) {
      wx.showToast({ title: '未选择文件', icon: 'none' });
    }
  },
  uploadBiddingFile(file) {
    const app = getApp();
    const token = getToken();
    const apiBase = app.globalData.apiBase;
    this.setData({ biddingUploading: true, biddingStatus: '文件上传中...' });
    wx.uploadFile({
      url: `${apiBase}/bidding/analyze/file?async_mode=true`,
      filePath: file.path,
      name: 'file',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        try {
          if (res.statusCode >= 400) {
            const payload = JSON.parse(res.data || '{}');
            const message = payload.detail || payload.error || '分析失败';
            this.setData({ biddingStatus: message, biddingResult: {} });
            wx.showToast({ title: message.toString(), icon: 'none' });
            return;
          }
          const data = JSON.parse(res.data || '{}');
          if (data.job_id) {
            this.setData({ biddingStatus: '模型处理中，请稍候...' });
            this.pollBiddingJob(data.job_id);
          } else if (data.result) {
            this.setData({ biddingResult: data.result, biddingStatus: '分析完成' });
          } else {
            wx.showToast({ title: '创建任务失败', icon: 'none' });
            this.setData({ biddingStatus: '' });
          }
        } catch (error) {
          wx.showToast({ title: '服务器响应异常', icon: 'none' });
          this.setData({ biddingStatus: '' });
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' });
        this.setData({ biddingStatus: '' });
      },
      complete: () => {
        this.setData({ biddingUploading: false });
      }
    });
  },
  pollBiddingJob(jobId) {
    const app = getApp();
    const token = getToken();
    const apiBase = app.globalData.apiBase;
    wx.request({
      url: `${apiBase}/bidding/jobs/${jobId}`,
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        if (res.statusCode === 200) {
          const data = res.data;
          if (data.status === 'completed') {
            this.setData({
              biddingResult: data.result || {},
              biddingStatus: '分析完成 ✅'
            });
          } else if (data.status === 'failed') {
            this.setData({ biddingStatus: data.error || '分析失败' });
          } else {
            this.setData({ biddingStatus: '模型处理中...' });
            setTimeout(() => this.pollBiddingJob(jobId), POLL_INTERVAL);
          }
        } else {
          wx.showToast({ title: '轮询失败', icon: 'none' });
        }
      },
      fail: () => {
        setTimeout(() => this.pollBiddingJob(jobId), POLL_INTERVAL);
      }
    });
  },
  async onPickWorkloadFile() {
    try {
      const res = await wx.chooseMessageFile({ count: 1, type: 'file' });
      if (!res.tempFiles?.length) return;
      this.uploadWorkloadFile(res.tempFiles[0]);
    } catch (error) {
      wx.showToast({ title: '未选择文件', icon: 'none' });
    }
  },
  uploadWorkloadFile(file) {
    const app = getApp();
    const token = getToken();
    const apiBase = app.globalData.apiBase;
    this.setData({ workloadUploading: true, workloadStatus: '任务创建中...' });
    wx.uploadFile({
      url: `${apiBase}/workload/analyze`,
      filePath: file.path,
      name: 'file',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        try {
          if (res.statusCode >= 400) {
            const payload = JSON.parse(res.data || '{}');
            const message = payload.detail || payload.error || '提交失败';
            this.setData({ workloadStatus: message, workloadResult: '' });
            wx.showToast({ title: message.toString(), icon: 'none' });
            return;
          }
          const data = JSON.parse(res.data || '{}');
          if (data.id) {
            this.setData({
              workloadStatus: `任务 #${data.id} 已提交，状态：${data.status}`,
              workloadResult: '请到任务页面查看详细结果。'
            });
          } else {
            this.setData({ workloadStatus: '任务提交成功', workloadResult: JSON.stringify(data) });
          }
        } catch (error) {
          wx.showToast({ title: '解析响应失败', icon: 'none' });
          this.setData({ workloadStatus: '' });
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' });
        this.setData({ workloadStatus: '' });
      },
      complete: () => {
        this.setData({ workloadUploading: false });
      }
    });
  },
  async onPickCostingFile() {
    try {
      const res = await wx.chooseMessageFile({ count: 1, type: 'file' });
      if (!res.tempFiles?.length) return;
      this.uploadCostingFile(res.tempFiles[0]);
    } catch (error) {
      wx.showToast({ title: '未选择文件', icon: 'none' });
    }
  },
  uploadCostingFile(file) {
    const app = getApp();
    const token = getToken();
    const apiBase = app.globalData.apiBase;
    this.setData({ costingUploading: true, costingStatus: '任务创建中...' });
    wx.uploadFile({
      url: `${apiBase}/costing/analyze`,
      filePath: file.path,
      name: 'file',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        try {
          if (res.statusCode >= 400) {
            const payload = JSON.parse(res.data || '{}');
            const message = payload.detail || payload.error || '提交失败';
            this.setData({ costingStatus: message, costingResult: '' });
            wx.showToast({ title: message.toString(), icon: 'none' });
            return;
          }
          const data = JSON.parse(res.data || '{}');
          if (data.id) {
            this.setData({
              costingStatus: `任务 #${data.id} 已提交，状态：${data.status}`,
              costingResult: '请到任务页面查看详细结果。'
            });
          } else {
            this.setData({ costingStatus: '任务提交成功', costingResult: JSON.stringify(data) });
          }
        } catch (error) {
          wx.showToast({ title: '解析响应失败', icon: 'none' });
          this.setData({ costingStatus: '' });
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' });
        this.setData({ costingStatus: '' });
      },
      complete: () => {
        this.setData({ costingUploading: false });
      }
    });
  }
});
