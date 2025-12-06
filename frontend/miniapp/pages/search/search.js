const api = require('../../utils/api');

Page({
    data: {
        tabs: ['查合同', '查资质', '查知产', '查人员', '查公司'],
        activeTab: 0,
        searchQuery: '',
        placeholderText: '合同名称、行业、客户名称、合同编号..',
        results: [],
        loading: false,
        hasMore: true,
        page: 0,
        limit: 20,
        // Filter State
        showFilter: false,
        hasActiveFilters: false,
        filters: {
            industry: '',
            contractTypeIndex: 0,
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
            businessTypeIndex: 0,

            // New Company Filters
            companyStatus: '',
            setupDateStart: '',
            setupDateEnd: '',
            capitalMin: '',
            capitalMax: ''
        },
        // Initialize Options to prevent crash
        contractTypeOptions: ['不限', '固定金额', '时间资源', '计件计量', '转售业务', '混合模式'],
        ipCategoryOptions: ['不限', '软件著作权', '软件产品', '专利', '技术查新', '域名', '商标', 'APP', '小程序'],
        businessTypeOptions: ['不限', '无', 'ITO业务', '教育业务', '通力业务', '投资业务', '云网业务', '智慧业务', '资产项目', '海外及其他业务', '研究院业务', '网络业务', '体外资产项目'],

        // Quick Tags State
        quickTags: {
            fp: false,
            time: null, // '3', '5'
            amount: null, // '300', '500', ...
            status: null, // 'completed'
            group: null, // Default null to show all
            ipCategory: null // 'patent', 'copyright', 'trademark'
        },
        // Detail Popup State
        showDetail: false,
        selectedContract: null,
        showCompanyDetail: false,
        selectedCompany: null,
        showQualDetail: false,
        selectedQual: null,
        showIPDetail: false,
        selectedIP: null,
        showPersonnelDetail: false,
        selectedPersonnel: null
    },

    onLoad(options) {
        if (options.tab) {
            const tabIndex = parseInt(options.tab) || 0;
            this.setData({ activeTab: tabIndex });
            this.updatePlaceholder(tabIndex);
        } else if (options.q) {
            this.setData({ searchQuery: options.q });
            this.performSearch();
        }

        // Auto-search for Company tab if active
        if (this.data.activeTab === 4) {
            this.performSearch();
        }
    },

    onShow() {
        const app = getApp();
        if (app.globalData.activeSearchTab) {
            const tabMap = {
                'contracts': 0,
                'qualifications': 1,
                'ip': 2,
                'personnel': 3,
                'company': 4
            };
            const tabName = app.globalData.activeSearchTab;
            const tabIndex = tabMap[tabName];

            if (tabIndex !== undefined) {
                this.setData({ activeTab: tabIndex });
                this.updatePlaceholder(tabIndex);

                // For Company tab, auto search if empty results
                if (tabIndex === 4 && this.data.results.length === 0) {
                    this.performSearch();
                }
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
            hasMore: true,
            page: 0,
            filters: { // Reset filters
                industry: '', contractTypeIndex: 0, customer: '', status: '', minAmount: '', maxAmount: '',
                personnelStatus: '', personnelCompany: '', personnelDegree: '', personnelCertificate: '',
                companyName: '', companyNumber: '', ipCategoryIndex: 0, businessTypeIndex: 0,
                companyStatus: '', setupDateStart: '', setupDateEnd: '', capitalMin: '', capitalMax: ''
            },
            quickTags: { // Reset quickTags
                fp: false, time: null, amount: null, status: null, group: null, ipCategory: null
            },
            searchQuery: '' // Clear query when switching
        });
        this.updatePlaceholder(index);

        // Auto-search for Company tab (Index 4)
        this.setData({
            hasActiveFilters: false // Reset flag
        });

        if (index === 4) {
            this.performSearch();
        }
    },

    updatePlaceholder(index) {
        const placeholders = [
            '合同名称、行业、客户名称、合同编号..',
            '资质名称、公司名称...',
            '知识产权名称、公司名称...',
            '员工姓名、证书名称',
            '公司编码、公司名称、组织机构代码、法人'
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
                contractTypeIndex: 0,
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
                businessTypeIndex: 0,
                companyStatus: '',
                setupDateStart: '',
                setupDateEnd: '',
                capitalMin: '',
                capitalMax: ''
            },
            hasActiveFilters: false
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
            text = `合同编号: ${item.contract_number || '-'} \n合同名称: ${item.contract_title || item.project_name} \n客户: ${item.customer_name || '-'} \n金额: ${item.contract_amount || '-'} \n签订时间: ${item.signing_date || '-'} `;
        } else if (this.data.activeTab === 1 || this.data.activeTab === 2) { // Qual/IP
            text = `名称: ${item.qualification_name} \n公司: ${item.company_name} \n类型: ${item.business_type || '-'} `;
        } else if (this.data.activeTab === 4) { // Company
            text = `公司名称: ${item.name}\n公司编号: ${item.code || '-'}\n统一信用代码: ${item.nuccn || '-'}`;
        } else { // Personnel
            text = `姓名: ${item.name} \n工号: ${item.employee_no || '-'} \n公司: ${item.company || '-'} `;
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
        // Allow empty query if filters are set.
        const { searchQuery, activeTab, filters, quickTags } = this.data;

        // Check if any filter is active
        const hasFilter = Object.values(filters).some(v => v) ||
            quickTags.fp || quickTags.time || quickTags.amount || quickTags.status ||
            quickTags.group || quickTags.ipCategory;

        if (!searchQuery.trim() && !hasFilter && activeTab !== 4) {
            wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
            return;
        }

        this.setData({ loading: true, page: 0, results: [] });

        try {
            // DEBUG: Show Params
            console.log(`Searching Tab ${activeTab} with query: ${searchQuery}`);

            const result = await this.searchByTab(activeTab, searchQuery, 0);

            // DEBUG: Alert Result Count (Remove before production)
            // wx.showModal({
            //    title: `Tab ${activeTab} Result`,
            //    content: `Count: ${result.results ? result.results.length : 0}\nTotal: ${result.total}`,
            //    showCancel: false
            // });

            const processedResults = this.processResults(result.results || []);

            if (processedResults.length === 0) {
                // wx.showToast({ title: '暂无数据', icon: 'none' });
            }

            this.setData({
                results: processedResults,
                hasMore: (result.total || 0) > this.data.limit,
                loading: false
            });
        } catch (error) {
            console.error("Search Error:", error);
            this.setData({ loading: false });
            wx.showToast({ title: '搜索失败', icon: 'none' });
        }
    },

    // 根据标签搜索
    async searchByTab(tabIndex, query, offset) {
        const { filters, quickTags, limit } = this.data;
        let params = {
            q: query,
            limit: limit,
            offset: offset
        };

        // Construct params specifically for each tab to avoid filter polling
        // Construct params specifically for each tab to avoid filter polling
        switch (tabIndex) {
            case 0: // Contracts
                if (quickTags.fp) params.is_fp = 'true';
                if (quickTags.status === 'completed') params.status = '已完结';
                if (quickTags.time) {
                    const years = parseInt(quickTags.time);
                    const date = new Date();
                    date.setFullYear(date.getFullYear() - years);
                    params.start_date = date.toISOString().split('T')[0];
                }
                if (quickTags.amount) params.min_amount = parseInt(quickTags.amount) * 10000;

                // Contract Filters (Drawer)
                const cType = this.data.contractTypeOptions[filters.contractTypeIndex];
                if (cType && cType !== '不限') params.contract_type = cType;
                if (filters.industry) params.industry = filters.industry;
                if (filters.customer) params.customer = filters.customer;
                if (filters.status) params.status = filters.status; // Explicit Status Filter
                if (filters.minAmount) params.min_amount = parseFloat(filters.minAmount) * 10000;
                if (filters.maxAmount) params.max_amount = parseFloat(filters.maxAmount) * 10000;

                return await api.searchContracts(params);

            case 1: // Qualifications
                if (quickTags.group === '1100') params.company_code = '1100'; // Corrected to company_code
                if (quickTags.notExpired) params.is_expired = 'false';

                // Business Type
                const qualBusType = this.data.businessTypeOptions[filters.businessTypeIndex];
                if (qualBusType && qualBusType !== '不限') params.business_type = qualBusType;

                return await api.searchQualifications(params);

            case 2: // IP
                if (quickTags.group === '1100') params.company_code = '1100';
                if (quickTags.notExpired) params.is_expired = 'false';
                if (filters.companyName) params.company_name = filters.companyName;
                if (filters.companyNumber) params.company_number = filters.companyNumber;

                // IP Category (Priority: Filter Picker > Quick Tag)
                const ipCat = this.data.ipCategoryOptions[filters.ipCategoryIndex];
                if (ipCat && ipCat !== '不限') {
                    params.business_type = ipCat; // Backend checks business_type
                } else if (quickTags.ipCategory) {
                    const map = {
                        'patent': '专利',
                        'software_product': '软件产品',
                        'copyright': '软件著作权',
                        'trademark': '商标'
                    };
                    params.business_type = map[quickTags.ipCategory] || quickTags.ipCategory;
                }

                // Business Type
                const ipBusType = this.data.businessTypeOptions[filters.businessTypeIndex];
                if (ipBusType && ipBusType !== '不限') params.business_type = ipBusType;

                return await api.searchIP(params);

            case 3: // Personnel
                if (filters.personnelCompany) params.company = filters.personnelCompany;
                if (filters.personnelStatus) params.status = filters.personnelStatus;
                if (filters.personnelDegree) params.degree = filters.personnelDegree;
                if (filters.personnelCertificate) params.certificate_name = filters.personnelCertificate;
                return await api.searchPersonnel(params);

            case 4: // Company
                if (filters.companyStatus) params.operating_state = filters.companyStatus; // Updated to companyStatus
                if (filters.setupDateStart) params.start_date = filters.setupDateStart; // Corrected param name start_date
                if (filters.setupDateEnd) params.end_date = filters.setupDateEnd; // Corrected param name end_date
                if (filters.capitalMin) params.capital_min = parseFloat(filters.capitalMin); // Corrected param name
                if (filters.capitalMax) params.capital_max = parseFloat(filters.capitalMax); // Corrected param name

                return await api.searchCompanies(params);

            default:
                return { results: [], total: 0 };
        }
    },

    // --- Picker Handlers ---
    bindContractTypeChange(e) {
        this.setData({
            'filters.contractTypeIndex': e.detail.value
        });
        this.performSearch(); // Optional: auto search on change
    },

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

    bindDateChange(e) {
        const field = e.currentTarget.dataset.field;
        this.setData({
            [`filters.${field}`]: e.detail.value
        });
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

            const processedResults = this.processResults(result.results || []);
            this.setData({
                results: [...this.data.results, ...processedResults],
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

    processResults(results) {
        if (!results) return [];
        return results.map(item => {
            // Contract Type Abbreviation
            if (item.contract_type) {
                const typeMap = {
                    '固定金额': 'FP',
                    '时间资源': 'TM',
                    '混合模式': '混',
                    '转售业务': '转',
                    '计件计量': '计'
                };
                item.short_type = typeMap[item.contract_type] || item.contract_type;
            }

            // Parse Customer Name (Remove Industry)
            if (item.customer_name) {
                const { customerName } = this.parseCustomerInfo(item.customer_name);
                item.display_customer = customerName;
            } else {
                item.display_customer = '-';
            }

            return item;
        });
    },

    // --- Detail Popup Logic ---
    showContractDetail(e) {
        const item = e.currentTarget.dataset.item;

        // Parse Customer and Industry
        const { customerName, industry } = this.parseCustomerInfo(item.customer_name);

        // Use parsed industry if available, otherwise fallback to item.industry
        const displayIndustry = industry || item.industry;
        const displayCustomer = customerName || item.customer_name;

        // Create a display object to avoid mutating original item too much
        const displayContract = {
            ...item,
            display_customer: displayCustomer,
            display_industry: displayIndustry
        };

        this.setData({
            selectedContract: displayContract,
            showDetail: true
        });
    },

    parseCustomerInfo(fullName) {
        if (!fullName) return { customerName: '', industry: '' };

        // Match the last occurrence of content inside full-width parentheses
        // Regex: /（([^）]+)）$/
        // Note: Using full-width parenthesis as per user example
        const match = fullName.match(/（([^）]+)）$/);

        if (match) {
            const industry = match[1].trim();
            const customerName = fullName.replace(match[0], '').trim();
            return { customerName, industry };
        }

        return { customerName: fullName, industry: '' };
    },

    closeContractDetail() {
        this.setData({
            showDetail: false,
            selectedContract: null
        });
    },

    // --- Company Detail Popup ---
    showCompanyDetail(e) {
        const item = e.currentTarget.dataset.item;
        this.setData({
            selectedCompany: item,
            showCompanyDetail: true
        });
    },

    closeCompanyDetail() {
        this.setData({
            showCompanyDetail: false,
            selectedCompany: null
        });
    },

    copyCompanyFull(e) {
        const item = e.currentTarget.dataset.item;
        let text = `公司名称: ${item.name}\n公司编号: ${item.code || '-'}\n` +
            `统一信用代码: ${item.nuccn || '-'}\n` +
            `法人: ${item.legal_person || '-'}\n` +
            `成立日期: ${item.setup_date || '-'}\n` +
            `注册资本: ${item.registered_capital || '-'}\n` +
            `经营状态: ${item.operating_state || '-'}\n` +
            `注册地址: ${item.registered_address || '-'}\n` +
            `经营范围: ${item.business_scope || '-'}`;

        wx.setClipboardData({
            data: text,
            success: () => wx.showToast({ title: '已复制全部', icon: 'success' })
        });
    },

    // --- Qual Detail Popup ---
    showQualDetail(e) {
        this.setData({
            selectedQual: e.currentTarget.dataset.item,
            showQualDetail: true
        });
    },
    closeQualDetail() {
        this.setData({
            showQualDetail: false,
            selectedQual: null
        });
    },
    copyQualFull(e) {
        const item = e.currentTarget.dataset.item;
        const text = `资质名称: ${item.qualification_name}\n公司: ${item.company_name}\n公司编号: ${item.company_code || '-'}\n类型: ${item.qualification_type || item.business_type || '-'}\n级别: ${item.qualification_level || '-'}\n编号: ${item.certificate_number || '-'}\n注册号: ${item.registration_no || '-'}\n发证机构: ${item.issue_organization || '-'}\n到期时间: ${item.expire_date || '-'} `;
        wx.setClipboardData({ data: text });
    },

    // --- IP Detail Popup ---
    showIPDetail(e) {
        this.setData({
            selectedIP: e.currentTarget.dataset.item,
            showIPDetail: true
        });
    },
    closeIPDetail() {
        this.setData({
            showIPDetail: false,
            selectedIP: null
        });
    },
    copyIPFull(e) {
        const item = e.currentTarget.dataset.item;
        const text = `知产名称: ${item.qualification_name}\n公司: ${item.company_name}\n公司编号: ${item.company_code || '-'}\n证书编号: ${item.certificate_number || '-'}\n专利类别: ${item.patent_category || '-'}\n发明人: ${item.inventor || '-'}\n申请日期: ${item.application_date || '-'}`;
        wx.setClipboardData({ data: text });
    },

    // --- Personnel Detail Popup ---
    showPersonnelDetail(e) {
        this.setData({
            selectedPersonnel: e.currentTarget.dataset.item,
            showPersonnelDetail: true
        });
    },
    closePersonnelDetail() {
        this.setData({
            showPersonnelDetail: false,
            selectedPersonnel: null
        });
    },
    copyPersonnelFull(e) {
        const item = e.currentTarget.dataset.item;
        let certs = (item.certificates || []).map(c => `${c.certificate_name} (${c.expire_date || '-'})`).join('\n');
        const text = `姓名: ${item.name}\n工号: ${item.employee_no || '-'}\n公司: ${item.company || '-'}\n学历: ${item.degree || '-'}\n学校: ${item.school || '-'}\n\n证书:\n${certs}`;
        wx.setClipboardData({ data: text });
    }
});
