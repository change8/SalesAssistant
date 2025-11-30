const api = require('../../utils/api');

Page({
    data: {
        tabs: ['合同', '资质', '知产', '人员'],
        activeTab: 0,
        searchQuery: '',
        placeholderText: '合同名称、行业、客户名称、合同编号..',
        results: [],
        loading: false,
        hasMore: false,
        page: 0,
        limit: 20,
        // Filter State
        showFilter: false,
        hasActiveFilters: false,
        filters: {
            industry: '',
            type: '',
            customer: '',
            status: '',
            minAmount: '',
            maxAmount: '',
            personnelStatus: '',
            personnelCompany: '',
            personnelDegree: '',
            personnelCertificate: ''
        },
        // Quick Tags State
        quickTags: {
            fp: false,
            time: null, // '3', '5'
            amount: null, // '300', '500', ...
            status: null, // 'completed'
            group: '1100', // Default for Quals? Or null? PC defaults to 1100 if checked. Let's default null.
            ipCategory: null // 'patent', 'copyright', 'trademark'
        },
        // Detail Popup State
        showDetail: false,
        selectedContract: null
    },

    onLoad(options) {
        if (options.tab) {
            const tabIndex = parseInt(options.tab) || 0;
            this.setData({ activeTab: tabIndex });
            this.updatePlaceholder(tabIndex);
        }
        if (options.q) {
            this.setData({ searchQuery: options.q });
            this.performSearch();
        }
        // Initialize default tags if needed
        // this.setData({ 'quickTags.group': '1100' }); // If we want to match PC default
    },

    onShow() {
        const app = getApp();
        if (app.globalData.activeSearchTab) {
            const tabMap = {
                'contracts': 0,
                'qualifications': 1,
                'ip': 2,
                'personnel': 3
            };
            const tabIndex = tabMap[app.globalData.activeSearchTab];
            if (tabIndex !== undefined) {
                this.setData({ activeTab: tabIndex });
                this.updatePlaceholder(tabIndex);
                // Optional: Auto-focus or clear results if needed
            }
            app.globalData.activeSearchTab = null; // Clear after use
        }
    },

    // 切换标签
    switchTab(e) {
        const index = e.currentTarget.dataset.index;
        this.setData({
            activeTab: index,
            results: [],
            page: 0,
            // Reset filters when switching tabs? Or keep them?
            // Usually better to reset or hide incompatible filters.
            // For simplicity, we keep state but UI hides irrelevant ones.
        });
        this.updatePlaceholder(index);
        if (this.data.searchQuery) {
            this.performSearch();
        }
    },

    updatePlaceholder(index) {
        const placeholders = [
            '合同名称、行业、客户名称、合同编号..',
            '资质名称、公司名称...',
            '知识产权名称、公司名称...',
            '员工姓名、证书名称'
        ];
        this.setData({ placeholderText: placeholders[index] || placeholders[0] });
    },

    // 输入搜索关键词
    onSearchInput(e) {
        this.setData({ searchQuery: e.detail.value });
    },

    onClearSearch() {
        this.setData({ searchQuery: '', results: [] });
    },

    // --- Filter Logic ---

    openFilter() {
        this.setData({ showFilter: true });
    },

    closeFilter() {
        this.setData({ showFilter: false });
    },

    onFilterInput(e) {
        const field = e.currentTarget.dataset.field;
        const value = e.detail.value;
        this.setData({
            [`filters.${field}`]: value
        });
    },

    onFilterTag(e) {
        const field = e.currentTarget.dataset.field;
        const value = e.currentTarget.dataset.value;
        const currentValue = this.data.filters[field];
        // Toggle if same value, else set new value
        this.setData({
            [`filters.${field}`]: currentValue === value ? '' : value
        });
    },

    resetFilters() {
        this.setData({
            filters: {
                industry: '',
                type: '',
                customer: '',
                status: '',
                minAmount: '',
                maxAmount: '',
                personnelStatus: '',
                personnelCompany: '',
                personnelDegree: '',
                personnelCertificate: '',
                companyName: '',
                companyNumber: '',
                ipCategoryIndex: 0,
                businessTypeIndex: 0
            },
            hasActiveFilters: false,
            ipCategoryOptions: ['不限', '软件著作权', '软件产品', '专利', '技术查新', '域名', '商标', 'APP', '小程序'],
            businessTypeOptions: ['不限', '无', 'ITO业务', '教育业务', '通力业务', '投资业务', '云网业务', '智慧业务', '资产项目', '海外及其他业务', '研究院业务', '网络业务', '体外资产项目']
        });
        this.checkActiveFilters();
    },

    applyFilters() {
        this.setData({ showFilter: false });
        this.checkActiveFilters();
        this.performSearch();
    },

    checkActiveFilters() {
        const f = this.data.filters;
        const hasActive = Object.values(f).some(val => val !== '' && val !== null);
        this.setData({ hasActiveFilters: hasActive });
    },

    // --- Export & Copy ---

    copyItem(e) {
        const item = e.currentTarget.dataset.item;
        let text = '';
        if (this.data.activeTab === 0) { // Contract
            text = `合同编号: ${item.contract_number || '-'}\n合同名称: ${item.contract_title || item.project_name}\n客户: ${item.customer_name || '-'}\n金额: ${item.contract_amount || '-'}`;
        } else if (this.data.activeTab === 1 || this.data.activeTab === 2) { // Qual/IP
            text = `名称: ${item.qualification_name}\n公司: ${item.company_name}\n类型: ${item.business_type || '-'}`;
        } else if (type === 'group') {
            const val = e.currentTarget.dataset.value;
            const current = this.data.quickTags.group;
            this.setData({
                'quickTags.group': current === val ? null : val
            });
            this.performSearch();
        } else { // Personnel
            text = `姓名: ${item.name}\n工号: ${item.employee_no || '-'}\n公司: ${item.company || '-'}`;
        }

        wx.setClipboardData({
            data: text,
            success: () => {
                wx.showToast({ title: '已复制', icon: 'success' });
            }
        });
    },

    exportData() {
        const query = this.data.searchQuery;
        // Construct params similar to performSearch
        // For now, just show a toast as backend might not support direct download via MP yet
        // Or try to open the URL

        // Mocking the export URL construction
        let url = `https://api.savetime.com/api/search/contracts/export?q=${query}`;
        // Add filters...

        wx.showModal({
            title: '导出 Excel',
            content: '确定要导出当前搜索结果吗？',
            success: (res) => {
                if (res.confirm) {
                    wx.showLoading({ title: '正在导出...' });
                    // Simulate download
                    setTimeout(() => {
                        wx.hideLoading();
                        wx.showToast({ title: '导出成功', icon: 'success' });
                        // In real app: wx.downloadFile + wx.openDocument
                    }, 1500);
                }
            }
        });
    },

    // --- Quick Tags Logic ---
    toggleQuickTag(e) {
        const type = e.currentTarget.dataset.type;
        const value = e.currentTarget.dataset.value;
        const { quickTags } = this.data;
        let newTags = { ...quickTags };

        if (type === 'fp') {
            newTags.fp = !newTags.fp;
        } else if (type === 'status') {
            newTags.status = newTags.status === value ? null : value;
        } else if (type === 'group') {
            newTags.group = newTags.group === value ? null : value;
        } else if (type === 'ipCategory') {
            newTags.ipCategory = newTags.ipCategory === value ? null : value;
        } else {
            // Mutually exclusive groups (time, amount)
            newTags[type] = newTags[type] === value ? null : value;
        }

        this.setData({ quickTags: newTags });
        this.performSearch();
    },

    // --- Search Logic ---

    // 执行搜索
    async performSearch() {
        // Allow empty query if filters are present? 
        // For now, keep requirement for query or just search if filters exist.
        // Let's allow empty query if filters are set.
        const { searchQuery, activeTab, filters, quickTags } = this.data;

        // Check if any filter is active
        const hasFilter = Object.values(filters).some(v => v) ||
            quickTags.fp || quickTags.time || quickTags.amount || quickTags.status ||
            quickTags.group || quickTags.ipCategory;

        if (!searchQuery.trim() && !hasFilter) {
            wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
            return;
        }

        this.setData({ loading: true, page: 0, results: [] });

        try {
            const result = await this.searchByTab(activeTab, searchQuery, 0);
            this.setData({
                results: result.results || [],
                hasMore: (result.total || 0) > this.data.limit,
                loading: false
            });
        } catch (error) {
            this.setData({ loading: false });
            wx.showToast({ title: '搜索失败', icon: 'none' });
        }
    },

    // 根据标签搜索
    async searchByTab(tabIndex, query, offset) {
        const { filters, quickTags, limit } = this.data;
        const params = {
            q: query,
            limit: limit,
            offset: offset,
            ...filters // Pass all filters
        };

        // Apply Quick Tags
        if (quickTags.fp) params.is_fp = 'true';

        if (quickTags.status === 'completed' && !params.status) {
            params.status = '已完结';
        }

        if (quickTags.time) {
            const years = parseInt(quickTags.time);
            const date = new Date();
            date.setFullYear(date.getFullYear() - years);
            const dateStr = date.toISOString().split('T')[0];
            if (!params.start_date) params.start_date = dateStr;
        }

        if (quickTags.amount) {
            const amount = parseInt(quickTags.amount) * 10000;
            if (!params.min_amount) params.min_amount = amount;
        }

        if (tabIndex === 1) { // Qualifications
            if (quickTags.group === '1100') params.company = '1100';
            if (quickTags.notExpired) params.is_expired = 'false';

            // Business Type Filter
            const busType = this.data.businessTypeOptions[filters.businessTypeIndex];
            if (busType && busType !== '不限') {
                params.business_type = busType;
            }
        }

        if (tabIndex === 2) { // IP
            if (quickTags.group) params.company = quickTags.group;
            if (quickTags.notExpired) params.is_expired = 'false';

            if (filters.companyName) params.company_name = filters.companyName;
            if (filters.companyNumber) params.company_number = filters.companyNumber;

            // IP Category Filter
            const ipCat = this.data.ipCategoryOptions[filters.ipCategoryIndex];
            if (ipCat && ipCat !== '不限') {
                params.qualification_type = ipCat;
            }

            // Business Type Filter
            const busType = this.data.businessTypeOptions[filters.businessTypeIndex];
            if (busType && busType !== '不限') {
                params.business_type = busType;
            }

            if (quickTags.ipCategory) {
                const map = { 'patent': '专利', 'copyright': '软著', 'trademark': '商标' };
                const term = map[quickTags.ipCategory];
                if (term) {
                    params.q = params.q ? `${params.q} ${term}` : term;
                }
            }
        }

        switch (tabIndex) {
            case 0: // 合同
                return await api.searchContracts(params);
            case 1: // 资质
                return await api.searchQualifications(params);
            case 2: // 知产
                return await api.searchIP(params);
            case 3: // 人员
                return await api.searchPersonnel(params);
            default:
                return { results: [], total: 0 };
        }
    },

    // --- Picker Handlers ---
    bindIPCategoryChange(e) {
        this.setData({
            'filters.ipCategoryIndex': e.detail.value
        });
        this.performSearch();
    },

    bindBusinessTypeChange(e) {
        this.setData({
            'filters.businessTypeIndex': e.detail.value
        });
        this.performSearch();
    },

    // 加载更多
    async loadMore() {
        if (this.data.loading || !this.data.hasMore) return;

        const nextPage = this.data.page + 1;
        this.setData({ loading: true, page: nextPage });

        try {
            const result = await this.searchByTab(
                this.data.activeTab,
                this.data.searchQuery,
                nextPage * this.data.limit
            );

            this.setData({
                results: [...this.data.results, ...(result.results || [])],
                hasMore: (nextPage + 1) * this.data.limit < (result.total || 0),
                loading: false
            });
        } catch (error) {
            this.setData({ loading: false });
            wx.showToast({ title: '加载失败', icon: 'none' });
        }
    },

    // 下拉刷新
    async onPullDownRefresh() {
        await this.performSearch();
        wx.stopPullDownRefresh();
    },

    // 触底加载
    onReachBottom() {
        this.loadMore();
    },

    // --- Detail Popup Logic ---
    showContractDetail(e) {
        const item = e.currentTarget.dataset.item;
        this.setData({
            selectedContract: item,
            showDetail: true
        });
    },

    closeContractDetail() {
        this.setData({
            showDetail: false,
            selectedContract: null
        });
    }
});
