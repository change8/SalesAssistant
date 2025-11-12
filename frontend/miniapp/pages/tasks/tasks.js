const { request, getToken } = require('../../utils/request');

Page({
  data: {
    viewMode: 'active',
    loading: false,
    activeList: [],
    historyList: [],
    isLoggedIn: false
  },
  onShow() {
    wx.setNavigationBarTitle({ title: '任务中心' });
    const hasToken = !!getToken();
    this.setData({ isLoggedIn: hasToken });
    if (hasToken) {
      this.loadTasks();
    }
  },
  onGoRegister() {
    wx.navigateTo({ url: '/pages/register/register' });
  },
  onGoLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },
  async loadTasks() {
    this.setData({ loading: true });
    try {
      const [active, history] = await Promise.all([
        request({ url: '/tasks?limit=20', method: 'GET' }),
        request({ url: '/tasks/history?limit=100', method: 'GET' })
      ]);
      this.setData({
        activeList: (active.items || []).map(this.decorateTask),
        historyList: (history.items || []).map(this.decorateTask)
      });
    } catch (error) {
      console.error(error);
    } finally {
      this.setData({ loading: false });
    }
  },
  decorateTask(task) {
    const map = {
      bidding_analysis: '标书分析',
      workload_analysis: '工时拆分',
      costing_estimate: '成本测算'
    };
    return {
      ...task,
      task_type_label: map[task.task_type] || task.task_type
    };
  },
  onSwitchMode(e) {
    const { mode } = e.currentTarget.dataset;
    this.setData({ viewMode: mode });
  },
  onTapTask(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/task-detail/task-detail?id=${id}` });
  },
  onRefresh() {
    this.loadTasks();
  }
});
