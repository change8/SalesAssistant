const form = document.getElementById('analyze-form');
const fileInput = document.getElementById('excel-file');
const fileLabel = document.getElementById('file-label');
const statusArea = document.getElementById('status-area');
const submitBtn = document.getElementById('submit-btn');
const exportBtn = document.getElementById('export-btn');
const summarySection = document.getElementById('summary-section');
const summaryContent = document.getElementById('summary-content');
const sheetsSection = document.getElementById('sheets-section');
const sheetsContainer = document.getElementById('sheets-container');

let lastFile = null;
let lastConfig = null;

fileInput.addEventListener('change', () => {
  if (fileInput.files && fileInput.files.length > 0) {
    fileLabel.textContent = `已选择：${fileInput.files[0].name}`;
    lastFile = null;
    lastConfig = null;
    toggleExportButton(false);
  } else {
    fileLabel.textContent = '点击或拖拽 Excel 文件到此处';
    lastFile = null;
    lastConfig = null;
    toggleExportButton(false);
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!fileInput.files || fileInput.files.length === 0) {
    showStatus('请先选择 Excel 文件。', 'error');
    return;
  }

  const currentFile = fileInput.files[0];

  const requestPayload = {
    config: {
      strategy: form.strategy.value,
      model: form.model.value,
    },
  };

  if (form.total_limit.value !== '') {
    requestPayload.config.total_limit = Number(form.total_limit.value);
  }
  lastConfig = requestPayload;
  lastFile = currentFile;

  const formData = new FormData();
  formData.append('file', currentFile);
  formData.append('config', JSON.stringify(requestPayload));

  try {
    toggleLoading(true);
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const detail = await safeError(response);
      throw new Error(detail || '分析请求失败');
    }

    const data = await response.json();
    renderAnalysis(data);
    showStatus('分析完成。', 'success');
    toggleExportButton(true);
  } catch (error) {
    console.error(error);
    showStatus(error.message || '分析失败，请稍后再试。');
    toggleExportButton(false);
  } finally {
    toggleLoading(false);
  }
});

if (exportBtn) {
  exportBtn.addEventListener('click', async () => {
    if (!lastFile || !lastConfig) {
      showStatus('请先完成一次分析再导出。');
      return;
    }

    try {
      exportBtn.disabled = true;
      showStatus('正在生成 Excel，请稍候…', 'loading');

      const formData = new FormData();
      formData.append('file', lastFile);
      formData.append('config', JSON.stringify(lastConfig));

      const response = await fetch('/api/export', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const detail = await safeError(response);
        throw new Error(detail || '导出失败');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.download = _buildDownloadName(lastFile.name);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(downloadUrl);
      showStatus('Excel 导出完成。', 'success');
    } catch (error) {
      console.error(error);
      showStatus(error.message || '导出失败，请重试。');
    } finally {
      exportBtn.disabled = false;
    }
  });
}

function toggleLoading(isLoading) {
  submitBtn.disabled = isLoading;
  if (exportBtn) {
    exportBtn.disabled = isLoading || !lastFile;
  }
  showStatus(isLoading ? '正在分析，请稍候…' : '', isLoading ? 'loading' : undefined);
}

function toggleExportButton(visible) {
  if (!exportBtn) return;
  exportBtn.classList.toggle('hidden', !visible);
  exportBtn.disabled = !visible;
}

async function safeError(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') {
      return payload.detail;
    }
    return JSON.stringify(payload);
  } catch (error) {
    return response.statusText;
  }
}

function showStatus(message, variant = 'error') {
  statusArea.textContent = '';
  statusArea.className = 'status-area';
  if (!message) return;

  const span = document.createElement('span');
  span.textContent = message;
  span.classList.add(variant === 'success' ? 'success' : variant === 'loading' ? 'loading' : 'error');
  statusArea.appendChild(span);
}

function renderAnalysis(result) {
  const sheets = Array.isArray(result?.sheets) ? result.sheets : [];
  if (sheets.length === 0) {
    summarySection.classList.add('hidden');
    sheetsSection.classList.add('hidden');
    toggleExportButton(false);
    return;
  }

  renderSummary(sheets);
  renderSheets(sheets);
}

function renderSummary(sheets) {
  const totals = {};
  sheets.forEach((sheet) => {
    const byRole = sheet?.summary?.by_role || {};
    Object.entries(byRole).forEach(([role, value]) => {
      totals[role] = (totals[role] || 0) + Number(value || 0);
    });
  });

  summaryContent.innerHTML = '';
  Object.entries(totals).forEach(([role, value]) => {
    const card = document.createElement('div');
    card.className = 'summary-card';
    card.innerHTML = `<h3>${role}</h3><span>${formatNumber(value)} 人月</span>`;
    summaryContent.appendChild(card);
  });

  summarySection.classList.toggle('hidden', Object.keys(totals).length === 0);
}

function renderSheets(sheets) {
  sheetsContainer.innerHTML = '';

  sheets.forEach((sheet) => {
    const card = document.createElement('div');
    card.className = 'sheet-card';

    const limit = sheet?.summary?.limit ?? sheet.total_months;
    const headerHtml = `
      <div class="sheet-header">
        <h3>${escapeHtml(sheet.sheet_name || '未命名 Sheet')}</h3>
        <span class="badge">合计：${formatNumber(sheet.summary?.total_allocated)} / 限制：${limit != null ? `${formatNumber(limit)} 人月` : '未提供'}</span>
      </div>
    `;

    const roleSummary = document.createElement('div');
    roleSummary.className = 'role-summary';
    Object.entries(sheet.summary?.by_role || {}).forEach(([role, value]) => {
      const pill = document.createElement('span');
      pill.className = 'role-pill';
      pill.textContent = `${role}: ${formatNumber(value)} 人月`;
      roleSummary.appendChild(pill);
    });

    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-wrapper';
    const table = document.createElement('table');

    table.innerHTML = `
      <thead>
        <tr>
          <th style="width: 14%">项目/模块</th>
          <th style="width: 36%">业务需求说明</th>
          <th>产品</th>
          <th>前端</th>
          <th>后端</th>
          <th>测试</th>
          <th>运维</th>
          <th style="width: 20%">分析说明</th>
        </tr>
      </thead>
      <tbody>
        ${renderRows(sheet.projects || [])}
      </tbody>
    `;

    tableWrapper.appendChild(table);
    card.innerHTML = headerHtml;
    card.appendChild(roleSummary);
    card.appendChild(tableWrapper);

    sheetsContainer.appendChild(card);
  });

  sheetsSection.classList.remove('hidden');
}

function renderRows(projects) {
  return projects
    .map((project) => {
      const allocation = project.allocation || {};
      return `
        <tr>
          <td>${escapeHtml(project.project || '-')}</td>
          <td>${escapeHtml(project.requirement || '-')}</td>
          <td>${formatNumber(allocation.product)}</td>
          <td>${formatNumber(allocation.frontend)}</td>
          <td>${formatNumber(allocation.backend)}</td>
          <td>${formatNumber(allocation.test)}</td>
          <td>${formatNumber(allocation.ops)}</td>
          <td>${escapeHtml(allocation.analysis || project.allocation?.analysis || '-')}</td>
        </tr>
      `;
    })
    .join('');
}

function formatNumber(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '0.0';
  }
  return Number(value).toFixed(1);
}

function escapeHtml(text) {
  if (text === undefined || text === null) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function _buildDownloadName(originalName) {
  if (!originalName) {
    return 'splitworkload_analysis.xlsx';
  }
  const dotIndex = originalName.lastIndexOf('.');
  const stem = dotIndex > 0 ? originalName.slice(0, dotIndex) : originalName;
  return `${stem}_analysis.xlsx`;
}
