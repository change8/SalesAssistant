const { request } = require('./request');

// ===== Search APIs =====

/**
 * 搜索合同
 */
function searchContracts(params) {
    return request({
        url: '/search/contracts',
        method: 'GET',
        data: params // params now includes filters
    });
}

/**
 * 搜索资质
 */
function searchQualifications(params) {
    return request({
        url: '/search/qualifications',
        method: 'GET',
        data: params
    });
}

/**
 * 搜索知识产权
 */
function searchIP(params) {
    return request({
        url: '/search/assets',
        method: 'GET',
        data: {
            category: 'intellectual_property',
            ...params
        }
    });
}

/**
 * 搜索人员
 */
function searchPersonnel(params) {
    return request({
        url: '/search/employees',
        method: 'GET',
        data: params // params now includes filters
    });
}

/**
 * 搜索公司
 */
function searchCompanies(params) {
    return request({
        url: '/search/companies',
        method: 'GET',
        data: params
    });
}

// ===== Bidding APIs =====

/**
 * 分析标书
 * @param {string} filePath - 微信临时文件路径
 */
function analyzeBidding(filePath) {
    return new Promise((resolve, reject) => {
        const app = getApp();
        const token = app?.globalData?.token || '';
        const apiBase = app?.globalData?.apiBase || '';

        wx.uploadFile({
            url: `${apiBase}/bidding_v2/analyze`,
            filePath: filePath,
            name: 'file',
            header: {
                'Authorization': `Bearer ${token}`
            },
            success(res) {
                if (res.statusCode === 200) {
                    try {
                        const data = JSON.parse(res.data);
                        resolve(data);
                    } catch (e) {
                        reject(new Error('解析响应失败'));
                    }
                } else {
                    const detail = res.data?.detail || '分析失败';
                    wx.showToast({ title: detail, icon: 'none' });
                    reject(new Error(detail));
                }
            },
            fail(error) {
                wx.showToast({ title: '上传失败', icon: 'none' });
                reject(error);
            }
        });
    });
}

// ===== Format Utilities =====

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 格式化金额
 */
function formatAmount(amount) {
    if (!amount && amount !== 0) return '-';
    return `¥${Number(amount).toLocaleString('zh-CN')}`;
}

/**
 * 截断文本
 */
function truncate(text, length = 50) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

module.exports = {
    searchContracts,
    searchQualifications,
    searchIP,
    searchPersonnel,
    searchCompanies,
    analyzeBidding,
    formatDate,
    formatAmount,
    truncate
};
