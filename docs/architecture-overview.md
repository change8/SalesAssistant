# Sales Assistant 平台技术架构

> 本文档面向接手项目的研发成员，梳理整体架构、关键模块、核心流程与运行注意事项，便于快速熟悉代码库并规划迭代工作。

## 1. 总览

```
┌──────────────────────┐
│        前端层         │  原生 Web / 微信小程序
├──────────┬───────────┤
│  Web 控制台 │  MiniApp │
└──────┬─────┴─────┬────┘
       │             │HTTPS (REST + 静态资源)
┌──────▼─────────────▼───────┐
│          FastAPI 后端        │  backend/app/main.py
│  ├─ Auth & Core (配置/数据库) │
│  ├─ Modules.bidding          │ -> 调用 BiddingAssistant 子模块
│  ├─ Modules.workload         │ -> 基于 SplitWorkload 拆分工时
│  ├─ Modules.costing          │ -> 工时结果推导成本与报价
│  └─ Modules.tasks            │ -> 统一异步任务队列 API
└──────────┬──────────┬────────┘
           │            │
   ┌───────▼───────┐  ┌─▼────────────────┐
   │   SQLite/DB   │  │  外部 LLM 服务     │ DashScope / OpenAI / ...
   └───────────────┘  └──────────────────┘

      │            │ 文件解析 / Excel 处理
┌─────▼────┐   ┌───▼────────────────────┐
│BiddingAssistant│ ┆ SplitWorkload        │
│ 静态规则+LLM   │ ┆ Excel -> NESMA+LLM  │
└────────────┘   └────────────────────┘
```

### 代码布局

- `backend/app`：FastAPI 主应用，按功能模块拆分；`core` 负责配置、数据库、依赖注入、任务调度等横切逻辑。
- `BiddingAssistant`：历史投标助手子项目，包含文件解析、LLM prompt、规则集合、内存任务存储等，当前通过 `get_bidding_subapp()` 以子应用方式挂载。
- `SplitWorkload`：工时拆分引擎，负责 Excel 解析、NESMA 功能点分析、LLM 角色分配和导出能力。
- `frontend/web`：原生 HTML/CSS/JS 控制台，实现登录、任务提交、轮询与结果呈现。
- `frontend/miniapp`：小程序端代码，复用同一套 REST API（实验阶段）。
- `docs/`：文档合集；当前新增《技术架构》《TODO 列表》，便于知识沉淀。

## 2. 运行时关键组件

### 2.1 身份认证

- 入口：`backend/app/modules/auth`。
- 注册 / 登录接口使用手机号 + 密码，密码由 Passlib `bcrypt` 哈希并持久化至数据库。
- 认证方式：JWT（`Authorization: Bearer <token>`），有效期默认 12 小时，可在 `.env` 中配置。
- 所有业务路由通过 `Depends(get_current_user)` 注入鉴权。

### 2.2 异步任务队列

- 模块：`backend/app/modules/tasks`。
- 任务模型 `AnalysisTask` 持久化在数据库，字段包括 `status`, `request_payload`, `result_payload`, `error_message`。
- 各业务模块（标书、成本、工时）均通过 `TaskService.create_task` 创建 pending 任务，并使用 FastAPI `BackgroundTasks` 在线程池内执行。
- 前端轮询 `/api/tasks/{id}` 获取状态，页面可随时刷新或重新登录查看历史。
- 失败时会写入 `error_message`，便于提示和排障。

### 2.3 标书分析（BiddingAssistant）

- 入口：`backend/app/modules/bidding`，鉴权后转发到子应用。
- 主要流程：
  1. 解析上传文件（支持 PDF、DOCX、TXT，必要时走 OCR）。
  2. 调用 DashScope/OpenAI 表达式，按类别（废标项、评分项等）生成结构化 JSON。
  3. 结合原始 snippet 生成最终结果，由前端展示。
- 关键文件：
  - `BiddingAssistant/backend/analyzer/llm.py`：LLM 客户端，内置 JSON 解析重试。
  - `BiddingAssistant/backend/analyzer/framework.py`：类别定义。
  - `BiddingAssistant/backend/services/analyzer_service.py`：任务生命周期管理。

### 2.4 工时拆分（SplitWorkload）与成本估算

- `SplitWorkload/backend/app/core/excel.py`：基于 OpenPyXL 的 Excel 解析（避开 Pandas 对 numpy 的依赖）。
- `SplitWorkload/backend/app/core/ai.py`：NESMA 提示 + DashScope Qwen 调用，返回角色人月。
- `SplitWorkload/backend/app/services/workload_service.py`：组合解析与优化，暴露给 FastAPI。
- `backend/app/modules/workload/router.py`：负责上传 Excel、生成任务、解析结果。
- `backend/app/modules/costing/service.py`：读取工时结果，结合单价、税率和毛利率求出成本、报价、导出报表。

### 2.5 配置与环境

- 所有配置集中在 `.env`（或环境变量）里，通过 `pydantic-settings` 加载。
- 核心变量：
  - `SA_*` 系统基础配置（JWT、数据库、CORS 等）。
  - `BIDDING_ASSISTANT_*`、`SPLITWORKLOAD_*`：外部 LLM 接入参数；`*_TIMEOUT=0` 表示无限等待。
- 启动脚本 `start_backend.sh`：创建 venv → 安装依赖 → 启动 uvicorn，同时设置 `SA_ENABLE_EMBEDDINGS=0`, `SA_ENABLE_OCR=0` 避免本地缺失模型/OCR 时崩溃。

## 3. 数据流与请求链路

### 3.1 标书分析
1. 前端上传文件 → `/api/tasks/bidding/file`。
2. 后端保存任务，后台线程解析文件并调用 LLM。
3. LLM 响应 JSON → `_parse_adaptive_response` 校验后写回任务 `result_payload`。
4. 前端轮询任务状态，成功时展示结论、评分项、成本项、原文片段。

### 3.2 工时拆分 + 成本预估
1. 前端上传 Excel，附带费率、税率和目标毛利率。
2. 后端创建两个独立任务：工时拆分（workload）和成本测算（costing），均使用后台线程调用 LLM。
3. `SplitWorkload` 返回角色分配，计算器将其映射为成本、报价、导出表格。
4. 前端轮询并呈现 JSON 及摘要、下载链接。

### 3.3 认证与前端静态资源
- `/web/*` 静态资源由 `FastAPI.staticfiles` 提供，任何请求先访问登录界面。
- 登录成功后，`frontend/web/app.js` 会保存 JWT 到 `localStorage`，后续调用统一带上 `Authorization` 头。
- 任务刷新由 `monitorTask` 轮询实现，默认间隔 2.8s。

## 4. 开发与部署注意事项

- **依赖安装**：建议 Python 3.10+；`start_backend.sh` 会自动创建 `.venv`。如需在系统 Python 下运行，可手动执行 `pip install -r backend/requirements.txt`。
- **数据库迁移**：当前使用 SQLAlchemy + SQLite，建表在 `backend/app/core/database.py:init_db()` 中完成；若切换 PostgreSQL，需引入 Alembic 维护迁移。
- **长任务容错**：开启 `*_TIMEOUT=0` 会一直等待 LLM 返回，建议配合监控与失败重试策略；必要时可引入 Celery/Redis ，将任务外包到 worker。
- **LLM 响应异常**：如果模型返回非 JSON，可在任务 `error_message` 中查到具体报错，同时查看后台日志中记录的 `raw snippet`，调整 prompt 或对输出做 post-process。
- **静态前端构建**：目前使用原生文件；若迁移到框架（React/Vue），请确保构建后产物放在 `frontend/web/dist` 并更新静态目录。
- **微信小程序**：部署前需准备企业微信主体、域名备案和 HTTPS 证书，在 `wechat-miniapp.md` 有准备清单。

## 5. 术语与缩写

- **NESMA**：Netherlands Software Metrics Association 方法论，用于估算软件功能点，结合角色权重辅助工时拆分。
- **LLM**：Large Language Model，大模型服务提供商可为 DashScope（通义千问）、OpenAI、Azure OpenAI 等。
- **Async Task**：采用 FastAPI `BackgroundTasks` 的伪异步任务；长远计划引入消息队列实现真正的异步调度。

## 6. 常见问题（FAQ）

1. **为什么后端依赖 `numpy`？**
   OpenPyXL 对 numpy 可选依赖；为了避免缺失 wheel 导致崩溃，项目提供了 `numpy` stub（`numpy/__init__.py`）。如需真实运算，请在部署环境安装官方 numpy 并移除 stub。

2. **任务一直 pending？**
   检查 LLM Key 是否配置正确、外部网络是否可用；后台日志如出现 `ReadTimeout` 或 `LLM 响应解析失败`，需调整模型配置或提示词。

3. **如何扩展新的分析模块？**
   在 `backend/app/modules` 下新增目录，定义 router 与 service；如涉及 LLM，建议复用 TaskService，沿用异步任务模式。

---

如需进一步补充，请同步更新本文件并在 `docs/todo.md` 中列出后续工作计划。
