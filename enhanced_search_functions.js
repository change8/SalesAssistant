// ===== Enhanced Search Functions =====

// Global state for filters
let currentContractFilters = {};
let currentAssetsCategory = '';

// Contract Search with Filters
function openContractSearch() {
    document.getElementById('contractSearchModal').style.display = 'flex';
    document.getElementById('contractSearchInput').focus();

    // Add search listener
    const input = document.getElementById('contractSearchInput');
    input.addEventListener('input', debounce(searchContracts, 500));
}

function closeContractSearch() {
    document.getElementById('contractSearchModal').style.display = 'none';
    document.getElementById('contractSearchInput').value = '';
    clearContractFilters();
    document.getElementById('contractSearchResults').innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">请输入关键词开始搜索</p>';
}

function toggleContractFilters() {
    const panel = document.getElementById('contractFiltersPanel');
    const toggleText = document.getElementById('filterToggleText');
    const toggleIcon = document.getElementById('filterToggleIcon');

    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        toggleText.textContent = '隐藏筛选条件';
        toggleIcon.textContent = '▲';
    } else {
        panel.style.display = 'none';
        toggleText.textContent = '显示筛选条件';
        toggleIcon.textContent = '▼';
    }
}

function clearContractFilters() {
    document.getElementById('filterCustomer').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterTags').value = '';
    document.getElementById('filterIndustry').value = '';
    document.getElementById('filterMinAmount').value = '';
    document.getElementById('filterMaxAmount').value = '';
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    currentContractFilters = {};
    document.getElementById('activeFilters').innerHTML = '';
    searchContracts();
}

function applyContractFilters() {
    currentContractFilters = {
        customer: document.getElementById('filterCustomer').value,
        status: document.getElementById('filterStatus').value,
        tags: document.getElementById('filterTags').value,
        industry: document.getElementById('filterIndustry').value,
        min_amount: document.getElementById('filterMinAmount').value,
        max_amount: document.getElementById('filterMaxAmount').value,
        start_date: document.getElementById('filterStartDate').value,
        end_date: document.getElementById('filterEndDate').value
    };

    // Show active filters
    displayActiveFilters();

    // Trigger search
    searchContracts();
}

function displayActiveFilters() {
    const activeDiv = document.getElementById('activeFilters');
    const filterLabels = {
        customer: '客户',
        status: '状态',
        tags: '标签',
        industry: '行业',
        min_amount: '最小金额',
        max_amount: '最大金额',
        start_date: '开始日期',
        end_date: '结束日期'
    };

    let html = '';
    for (const [key, value] of Object.entries(currentContractFilters)) {
        if (value) {
            html += `<span style="display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-right: 8px; margin-bottom: 8px;">
            ${filterLabels[key]}: ${value}
            <button onclick="removeFilter('${key}')" style="background: none; border: none; margin-left: 4px; cursor: pointer; color: #0369a1;">×</button>
          </span>`;
        }
    }
    activeDiv.innerHTML = html;
}

function removeFilter(filterKey) {
    currentContractFilters[filterKey] = '';
    document.getElementById(`filter${filterKey.charAt(0).toUpperCase() + filterKey.slice(1).replace('_', '')}`).value = '';
    displayActiveFilters();
    searchContracts();
}

async function searchContracts() {
    const query = document.getElementById('contractSearchInput').value.trim();
    const resultsDiv = document.getElementById('contractSearchResults');

    if (!query && Object.values(currentContractFilters).every(v => !v)) {
        resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">请输入关键词或设置筛选条件开始搜索</p>';
        return;
    }

    resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">搜索中...</p>';

    try {
        // Build query string with all filters
        const params = new URLSearchParams();
        if (query) params.append('q', query);

        for (const [key, value] of Object.entries(currentContractFilters)) {
            if (value) params.append(key, value);
        }

        params.append('limit', '20');

        const data = await apiCall(`/search/contracts?${params.toString()}`);

        if (data.total === 0) {
            resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">未找到相关合同</p>';
            return;
        }

        let html = `<div style="margin-bottom: 12px;"><strong>找到 ${data.total} 条结果</strong></div>`;
        html += '<div style="display: flex; flex-direction: column; gap: 16px;">';

        data.results.forEach(contract => {
            html += `
            <div class="card" style="padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <h3 class="text-h3" style="margin: 0; flex: 1;">${contract.project_name}</h3>
                <span class="badge" style="background: ${contract.status && contract.status.includes('进行中') ? '#dcfce7' : '#e5e7eb'}; color: ${contract.status && contract.status.includes('进行中') ? '#166534' : '#6b7280'}; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                  ${contract.status || '未知'}
                </span>
              </div>
              <p class="text-sm" style="margin: 4px 0; color: var(--color-text-secondary);">
                <strong>客户：</strong>${contract.client_name || '未知'}
                ${contract.contract_number ? ` | <strong>编号：</strong>${contract.contract_number}` : ''}
              </p>
              ${contract.contract_amount ? `<p class="text-sm" style="margin: 4px 0;"><strong>合同金额：</strong>${contract.contract_amount}</p>` : ''}
              ${contract.signing_date ? `<p class="text-sm" style="margin: 4px 0;"><strong>签订日期：</strong>${contract.signing_date}</p>` : ''}
              ${contract.tags ? `<p class="text-sm" style="margin: 4px 0;"><strong>标签：</strong>${contract.tags}</p>` : ''}
              ${contract.project_description ? `<p class="text-sm" style="margin-top: 8px; color: var(--color-text-secondary);">${contract.project_description.substring(0, 200)}...</p>` : ''}
            </div>
          `;
        });

        html += '</div>';
        resultsDiv.innerHTML = html;
    } catch (err) {
        resultsDiv.innerHTML = `<p class="text-body" style="text-align: center; padding: 40px; color: red;">搜索失败: ${err.message}</p>`;
    }
}

// Assets (Qualifications/IP) Search
function openAssetsSearch() {
    document.getElementById('assetsSearchModal').style.display = 'flex';
    document.getElementById('assetsSearchInput').focus();

    // Add search listener
    const input = document.getElementById('assetsSearchInput');
    input.addEventListener('input', debounce(searchAssets, 500));
}

function closeAssetsSearch() {
    document.getElementById('assetsSearchModal').style.display = 'none';
    document.getElementById('assetsSearchInput').value = '';
    currentAssetsCategory = '';
    setAssetsCategory(''); // Reset to "all"
    document.getElementById('assetsSearchResults').innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">请输入关键词开始搜索</p>';
}

function setAssetsCategory(category) {
    currentAssetsCategory = category;

    // Update tab states
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active-tab'));
    if (category === '') {
        document.getElementById('assetsCatAll').classList.add('active-tab');
    } else if (category === 'qualification') {
        document.getElementById('assetsCatQual').classList.add('active-tab');
    } else if (category === 'intellectual_property') {
        document.getElementById('assetsCatIP').classList.add('active-tab');
    }

    // Trigger search if there's a query
    searchAssets();
}

async function searchAssets() {
    const query = document.getElementById('assetsSearchInput').value.trim();
    const resultsDiv = document.getElementById('assetsSearchResults');

    if (!query) {
        resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">请输入关键词开始搜索</p>';
        return;
    }

    resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">搜索中...</p>';

    try {
        const params = new URLSearchParams({
            q: query,
            limit: '20'
        });
        if (currentAssetsCategory) {
            params.append('category', currentAssetsCategory);
        }

        const data = await apiCall(`/search/assets?${params.toString()}`);

        if (data.total === 0) {
            resultsDiv.innerHTML = '<p class="text-body" style="text-align: center; padding: 40px;">未找到相关资质或知识产权</p>';
            return;
        }

        let html = `<div style="margin-bottom: 12px;"><strong>找到 ${data.total} 条结果</strong></div>`;
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;">';

        data.results.forEach(asset => {
            const isQualification = asset.category === 'qualification';
            const icon = isQualification ? '🏆' : '📜';
            const bgColor = isQualification ? '#dcfce7' : '#fef3c7';

            html += `
            <div class="card" style="padding: 16px;">
              <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="width: 40px; height: 40px; background: ${bgColor}; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                  ${icon}
                </div>
                <div style="flex: 1;">
                  <h3 class="text-h3" style="margin: 0; font-size: 15px;">${asset.qualification_name}</h3>
                  <p class="text-sm" style="margin: 2px 0; color: var(--color-text-secondary);">${asset.company_name}</p>
                </div>
              </div>
              ${asset.qualification_level ? `<p class="text-sm" style="margin: 4px 0;"><strong>等级：</strong>${asset.qualification_level}</p>` : ''}
              ${asset.business_type ? `<p class="text-sm" style="margin: 4px 0;"><strong>类型：</strong>${asset.business_type}</p>` : ''}
              ${asset.expire_date ? `<p class="text-sm" style="margin: 4px 0;"><strong>有效期至：</strong>${asset.expire_date}</p>` : ''}
            </div>
          `;
        });

        html += '</div>';
        resultsDiv.innerHTML = html;
    } catch (err) {
        resultsDiv.innerHTML = `<p class="text-body" style="text-align: center; padding: 40px; color: red;">搜索失败: ${err.message}</p>`;
    }
}

// Remove old qualification search functions (replaced by assets)
function openQualificationSearch() {
    // Redirect to assets search
    openAssetsSearch();
    setAssetsCategory('qualification');
}

function closeQualificationSearch() {
    closeAssetsSearch();
}
