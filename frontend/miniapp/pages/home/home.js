const { request, getToken } = require('../../utils/request');

const POLL_INTERVAL = 2500;

Page({
  data: {
    activeTab: 'bidding',
    biddingUploading: false,
    biddingStatus: '',
    biddingResult: {},
    workloadUploading: false,
    workloadStatus: '',
    workloadResult: '',
    costingUploading: false,
    costingStatus: '',
    costingResult: '',
    tasks: []
  },
  onShow() {
    if (!getToken()) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    wx.setNavigationBarTitle({ title: '销售助手' });
    this.onRefreshTasks();
  },
  onSwitchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    if (tab === 'tasks') {
      this.onRefreshTasks();
    }
  },
  async onPickBiddingFile() {
    try {
      const res = await wx.chooseMessageFile({ count: 1, type: 'file' });
      if (!res.tempFiles?.length) return;
      const file = res.tempFiles[0];
      this.uploadBiddingFile(file);
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
      header: {
        Authorization: `Bearer ${token}`
      },
      formData: {},
      success: (res) => {
        try {
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
      header: {
        Authorization: `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const data = res.data;
          if (data.status === 'completed') {
            this.setData({
              biddingResult: data.result || {},
              biddingStatus: '分析完成 ✅'
            });
            this.onRefreshTasks();
          } else if (data.status === 'failed') {
            this.setData({ biddingStatus: data.error || '分析失败' });
            this.onRefreshTasks();
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
      header: {
        Authorization: `Bearer ${token}`
      },
      formData: {},
      success: (res) => {
        try {
          const data = JSON.parse(res.data || '{}');
          if (data.id) {
            this.setData({
              workloadStatus: `任务 #${data.id} 已提交，状态：${data.status}`,
              workloadResult: '请在任务队列中查看详细结果。'
            });
            this.onRefreshTasks();
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
      header: {
        Authorization: `Bearer ${token}`
      },
      formData: {},
      success: (res) => {
        try {
          const data = JSON.parse(res.data || '{}');
          if (data.id) {
            this.setData({
              costingStatus: `任务 #${data.id} 已提交，状态：${data.status}`,
              costingResult: '请在任务队列中查看详细结果。'
            });
            this.onRefreshTasks();
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
  },
  async onRefreshTasks() {
    try {
      const data = await request({
        url: '/tasks',
        method: 'GET'
      });
      const items = (data.items || []).map((item) => ({
        ...item,
        task_type_label: this.mapTaskType(item.task_type)
      }));
      this.setData({ tasks: items });
    } catch (error) {
      console.error(error);
    }
  },
  mapTaskType(type) {
    switch (type) {
      case 'bidding_analysis':
        return '标书分析';
      case 'workload_analysis':
        return '工时拆分';
      case 'costing_estimate':
        return '成本估算';
      default:
        return type || '任务';
    }
  }
});
