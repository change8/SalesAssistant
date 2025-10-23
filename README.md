# Sales Assistant Platform

融合投标助手、工时拆分与成本预估的统一销售效率平台，目标是为销售团队提供一个可扩展的中台：支持标书分析、项目评估、费用估算，并为后续的报销助手、客户背调、名词解释等模块预留架构空间。项目包含统一的帐号体系、数据权限隔离、可配置的大模型调用以及一键启动脚本。

---

## 功能总览
- **账号体系**：手机号 + 密码注册/登录，支持找回密码（短信验证待接入），JWT 鉴权（计划扩展微信手机号授权）。
- **标书分析**：两步式流程（上传 → 进度&结果），输出“结论+投标要点+评分项+成本项”，支持查看原文定位。
- **FP 项目成本预估**：按人天成本测算总投入、含税成本与报价，支持毛利率控制、成本/报价表一键下载。
- **ITO 项目工时拆分**：解析 Excel 功能清单，支持人月/人天制，结合自定义角色单价输出汇总成本。
- **任务队列**：所有大模型任务统一纳入异步队列，前端提供“任务中心”查看进度、分类筛选与历史记录。
- **前端控制台**：统一 Web 页面提供登录、Tab 切换和移动端友好的展示；微信小程序提供同源能力。

---

## 部署快速开始

```bash
# 首次（在服务器）
git clone https://github.com/change8/SalesAssistant.git
cd SalesAssistant
sudo SA_DOMAIN=saleassisstant.chat SA_ADMIN_EMAIL=you@example.com ./deploy.sh

# 更新
sudo ./update.sh
```

部署脚本会安装依赖、配置 systemd + nginx、申请 Let's Encrypt 证书并启动服务。更多细节、DNS/HTTPS/微信小程序配置请参考 `ops/docs/deployment.md`。

若需自动化部署，仓库内置 GitHub Actions 工作流 `.github/workflows/deploy.yml`，在 Push 到 `main` 后会执行 `sudo ./update.sh`（需在仓库 Secrets 写入服务器 SSH 信息）。

---

## 架构概览
```
SalesAssistant/
├── backend/
│   ├── app/
│   │   ├── auth/           # 用户模型、密码加密、JWT 逻辑与 API
│   │   ├── core/           # 配置、数据库、依赖注入、应用工厂
│   │   ├── modules/
│   │   │   ├── bidding/    # 调用原投标助手分析服务并做用户隔离
│   │   │   ├── workload/   # 继承 SplitWorkload 的人月分析能力
│   │   │   └── costing/    # 基于人月结果计算成本
│   │   └── main.py         # FastAPI 入口，挂载静态前端
│   └── requirements.txt    # 统一依赖清单
├── frontend/
│   └── web/                # 登录 + 三大功能的原生静态页面
├── BiddingAssistant/        # 原投标助手代码（LLM 抽取、规则、前端原型）
├── SplitWorkload/           # 原工时拆分服务（Excel 解析、NESMA、导出）
├── .env.example             # 环境变量样例
└── start_backend.sh         # 一键创建虚拟环境并启动后端
```

技术选型：
- **后端**：FastAPI + SQLAlchemy + SQLite（可替换为 PostgreSQL），Passlib 处理密码哈希，PyJWT 做令牌。
- **AI 调用**：统一走外部大模型（可接入 OpenAI/Azure/Ollama/DashScope），所有模块取消启发式兜底并提供一致的异常提示。
- **前端**：原生 HTML/CSS/JS，快速展示；后续可替换为 React/Vue 或微信小程序。

---

## 快速开始
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，替换模型 API Key、数据库、JWT Secret 等

# 2. 一键启动后端（自动创建虚拟环境并安装依赖）
./start_backend.sh
```
默认服务地址：`http://127.0.0.1:8000`
- 统一控制台：`http://127.0.0.1:8000/web/`
- 健康检查：`GET /health`

如需自定义端口，可追加 uvicorn 参数：`./start_backend.sh --port 9000`。

---

## 环境配置
关键环境变量（`.env`）：
- `SA_JWT_SECRET`：JWT 签名，务必替换为随机值。
- `SA_DATABASE_URL`：默认 `sqlite:///./sales_assistant.db`，生产建议换成 PostgreSQL。
- `SA_CORS_ORIGINS`：JSON 数组，允许的前端域名。
- `BIDDING_ASSISTANT_*`：投标助手大模型配置。
- `SPLITWORKLOAD_*`：工时拆分/成本预估模型配置。

> 开发环境未填写真实 Key 时，投标助手会使用 `stub` 客户端并提示配置异常，需在具备模型可用性后再执行分析。

### 部署建议
- **云服务器**：建议 4 核 CPU / 8 GB 内存 / 60 GB SSD 起步；需具备公网 IPv4 和备案域名。
- **运行环境**：Python 3.10+、Node.js（用于打包前端）、Nginx 或 Caddy 反向代理、SQLite（小规模）或 PostgreSQL（推荐）。
- **HTTPS**：为满足微信小程序及浏览器安全策略，务必申请有效 TLS 证书（可使用 Let’s Encrypt）。
- **进程管理**：建议使用 `supervisor`、`systemd` 或 `pm2` 托管 `uvicorn` 进程，并配置自动重启。
- **日志与监控**：保留 `uvicorn` 访问/错误日志，结合云监控设置 CPU、内存、磁盘、LLM 调用失败告警。

---

## 主要 API
所有接口前缀默认为 `/api`。

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| Auth | POST | `/api/auth/register` | 注册新账号 |
| Auth | POST | `/api/auth/login` | 登录获取 JWT |
| Auth | GET  | `/api/auth/me` | 获取当前用户信息 |
| Bidding | POST | `/api/tasks/bidding/text` | 提交文本分析任务 |
| Bidding | POST | `/api/tasks/bidding/file` | 上传标书生成异步任务 |
| Bidding | GET  | `/api/bidding/jobs/{job_id}` | （完成后）按 ID 获取 LLM 输出与原文片段 |
| Workload | POST | `/api/workload/analyze` | 上传 Excel，输出人月拆分结果 |
| Workload | POST | `/api/workload/export` | 导出拆分结果为 Excel |
| Costing | POST | `/api/costing/analyze` | 上传 Excel + 费率，生成异步成本任务 |
| Tasks | GET | `/api/tasks` | 当前用户的任务列表（按创建时间倒序） |
| Tasks | GET | `/api/tasks/{task_id}` | 查看单个任务详情（状态/结果/错误） |

> 所有业务接口均要求 `Authorization: Bearer <token>` 请求头，投标任务记录也会按 `owner_id` 自动隔离。

---

## 前端使用指南
1. 首次访问 `/web/`，注册并登录账号。
2. 使用顶部 Tab 切换模块：
   - **标书分析**：上传标书即可进入进度页面，待分析完成后依次浏览“结论、投标要点、评分项、成本项”，可点击“查看原文”定位原文片段。
 - **FP 项目成本预估**：上传功能清单，设置统一人天成本/税率/产品费用/毛利率，可获得含税成本、报价建议以及成本表与报价表的下载。
  - **ITO 项目工时拆分**：上传同类清单，选择人月或人天制并录入角色单价，系统返回分角色工时及成本估算。
  - **任务队列**：在“任务队列”卡片内可刷新当前任务、追溯历史记录，点击任一任务可重新加载结果。
3. 结果面板同时保留原始 JSON 便于调试与二次集成。

### 微信小程序版本（实验中）
- 代码位于 `frontend/miniapp/`，提供登录、文件上传、进度展示与四类结果呈现的轻量小程序端。
- 使用前请在 `frontend/miniapp/config.js` 填写后端公网 HTTPS 地址，并在微信开发者工具导入该项目进行调试。
- 需将后端部署在具备备案的 HTTPS 域名下，并在微信公众平台配置 request/uploadFile/downloadFile 域名白名单。

---

## 后续规划
- **报销助手**：接入 OCR/规则校验，结合审批流与预算控制。
- **客户背调**：整合企业知识库或第三方 API（企查查等），形成客户画像卡片。
- **名词解释**：内置领域词典 + LLM 兜底，提升新手销售效率。
- **多模型交叉验证**：对工时与成本估算引入第二套模型策略，比较结果并给出可信区间/解释。
- **权限与审计**：扩展组织/团队维度，增加操作日志与数据加密策略。
- **小程序落地**：完善微信端 UI、自适应布局、真机调试及发布流程。

欢迎基于此架构继续拓展模块，复用统一的认证、存储与前端壳。

---

## 参考文档

- [技术架构总览](docs/architecture-overview.md)：组件划分、数据流、部署注意事项。
- [TODO / Backlog 列表](docs/todo.md)：待办事项与优先级记录。
- [微信小程序规划](docs/wechat-miniapp.md)：小程序落地准备与环境清单。
