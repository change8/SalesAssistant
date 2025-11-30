const api = require('../../utils/api');

Page({
    data: {
        uploading: false,
        analyzing: false,
        result: null
    },

    // 选择文件
    chooseFile() {
        wx.chooseMessageFile({
            count: 1,
            type: 'file',
            extension: ['pdf', 'doc', 'docx', 'txt'],
            success: (res) => {
                const file = res.tempFiles[0];

                // Check file size (max 10MB)
                if (file.size > 10 * 1024 * 1024) {
                    wx.showToast({ title: '文件大小不能超过10MB', icon: 'none' });
                    return;
                }

                this.uploadFile(file.path);
            },
            fail: () => {
                wx.showToast({ title: '选择文件失败', icon: 'none' });
            }
        });
    },

    // 上传并分析文件
    async uploadFile(filePath) {
        this.setData({ uploading: true, analyzing: true });

        try {
            const result = await api.analyzeBidding(filePath);

            // Pre-process requirements
            const requirements = (result.requirements || []).map(r => ({
                ...r,
                statusClass: this.getStatusClass(r.status),
                statusText: this.getStatusText(r.status)
            }));

            const caseRequirements = requirements.filter(r => r.category === 'case');
            const qualificationRequirements = requirements.filter(r => r.category === 'qualification');
            const personnelRequirements = requirements.filter(r => r.category === 'personnel');

            this.setData({
                result: result,
                caseRequirements,
                qualificationRequirements,
                personnelRequirements,
                uploading: false,
                analyzing: false
            });
            wx.showToast({ title: '分析完成', icon: 'success' });
        } catch (error) {
            console.error('Analysis failed:', error);
            this.setData({ uploading: false, analyzing: false });
            wx.showToast({ title: '分析失败', icon: 'none' });
        }
    },

    // 重置
    reset() {
        this.setData({
            uploading: false,
            analyzing: false,
            result: null
        });
    },

    // 获取需求列表
    getRequirements(category) {
        if (!this.data.result || !this.data.result.requirements) return [];
        return this.data.result.requirements.filter(r => r.category === category);
    },

    // 获取状态样式
    getStatusClass(status) {
        if (status === 'satisfied') return 'tag-success';
        if (status === 'unsatisfied') return 'tag-danger';
        return 'tag-warning';
    },

    // 获取状态文本
    getStatusText(status) {
        if (status === 'satisfied') return '✅ 满足';
        if (status === 'unsatisfied') return '❌ 不满足';
        return '⚠️ 需人工核对';
    }
});
