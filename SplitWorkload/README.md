# SplitWorkload

SplitWorkload 是一个端到端的智能人月分配平台：

- 解析多 Sheet 的 Excel 功能清单，识别需求描述/项目名称/角色列与合计行；
- 基于 NESMA 功能点分析 + 通义千问 Qwen3-Max 大模型做语义理解与造价估算；
- 在总人月限制下，将工作量拆分到产品、前端、后端、测试、运维；
- 自带浏览器界面（单页 HTML + 原生 JS）用于上传、配置策略、查看结果；
- 仅需启动 FastAPI 后端即可使用，默认集成前端页面。

## 快速开始

### 1. 准备 `.env`

复制项目根目录的 `.env.example` 为 `.env`，并填入实际密钥（示例已包含占位值）：

```bash
cp .env.example .env
```

修改 `.env` 确保 `SPLITWORKLOAD_MODEL_API_KEY` 为真实密钥。

如需自定义模型或超时，也可修改其它变量。

> **安全提示**：`.env` 已加入 `.gitignore`，不要把真实密钥提交到仓库。

### 2. 启动服务

项目根目录提供一条命令即可完成所有配置与启动：

```bash
./start_backend.sh
```

脚本会自动：

- 查找可用的 `python3.11`/`python3.10`，创建或更新虚拟环境；
- 安装 `backend/requirements.txt` 中的依赖；
- 启动 FastAPI（默认端口 `8000`）。

浏览器访问：

- 页面入口：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/api/health`

页面已内嵌上传、策略配置、结果展示等功能。

## 系统说明

### Excel 解析

- 自动定位「序号 / 项目名称 / 业务需求说明 / 产品 / 前端 / 后端 / 测试 / 运维 / 预估最低投入要求合计」等列；
- 跳过“合计/总计”行，将最后的合计数字视为人月限制；
- 行内角色列会被记录在元数据里，用于与模型结果比对（未来可用于校准）。

### 智能分析策略

1. 使用 `core.fpa.analyze_with_nesma_framework` 基于 NESMA 功能点方法推断功能类型、数据/交易复杂度、功能点估值与角色权重提示；
2. 构建带 NESMA 提示的 Prompt，调用 DashScope 兼容接口的 Qwen3-Max（可切换策略）；
3. 若模型不可用，则结合关键词统计 + NESMA 权重进行启发式分配，且给出降级原因；
4. `AllocationOptimizer` 会在总人月限制下等比缩放分配结果，并生成按角色的汇总数据。

### API 端点

- `GET /api/health`：健康检查；
- `POST /api/analyze`：multipart 上传 Excel，`config` 表单字段传 JSON（包含策略、模型、总限制等）。

### 页面能力

- Excel 拖拽上传 + 策略/模型配置；
- 全局角色汇总、逐 Sheet 结果展示；
- 显示大模型/启发式的分析说明与 NESMA 提示；
- 一键导出分析结果为 Excel。

## 测试

后端单元测试：

```bash
cd backend
source .venv/bin/activate  # 若已创建
pip install -r requirements.txt
pip install pytest
pytest
```

## 目录结构

```
backend/         FastAPI 服务、核心算法、Dockerfile
backend/tests/   后端单元测试
backend/app/templates 与 app/static 提供内置页面与资源
.env.example     模型配置样例
```

## 常见问题

- **密钥失效 / 权限不足**：检查 `.env` 是否填写正确，或在阿里云 DashScope 控制台确认 key 有权限访问 `qwen3-max`；
- **无法联网安装依赖**：首次运行需要外网以下载 pip/npm 包，可在有网络的环境初始化后再迁移；
- **Excel 字段差异**：若列名与截图差异较大，可扩展 `backend/app/core/excel.py` 中的关键词集合。

欢迎继续完善策略规则、导出能力或权限控制，以适配更多项目场景。
