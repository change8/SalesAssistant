# Sales Assistant Platform

融合投标助手、工时拆分与成本预估的统一销售效率平台，目标是为销售团队提供一个可扩展的中台：支持标书分析、项目评估、费用估算，并为后续的报销助手、客户背调、名词解释等模块预留架构空间。项目包含统一的帐号体系、数据权限隔离、可配置的大模型调用以及一键启动脚本。

---

## 功能总览
- **账号体系**：手机号 + 密码注册/登录，JWT 鉴权（计划扩展微信手机号授权）。
- **投标助手**：上传标书或粘贴文本，大模型解析关键条款、风险提示与标签（复用原投标助手规则与分析框架）。
- **工时拆分**：解析多 Sheet Excel 功能清单，结合 NESMA + LLM/启发式，输出产品/前端/后端/测试/运维人月估算。
- **成本预估**：在工时拆分基础上扩展为七个角色（架构师、项目经理、产品设计、前/后端、测试、实施），支持自定义费率与系数生成成本明细和汇总。
- **前端控制台**：统一 Web 页面提供登录、Tab 切换和结果展示；微信小程序对接计划中。

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
- **AI 调用**：投标助手使用原配置（可接入 OpenAI/Azure/Ollama），工时拆分/成本预估默认使用 DashScope Qwen 系列，提供启发式降级。
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
- `SPLITWORKLOAD_*`：工时拆分/成本预估模型或启发式配置。

> 开发环境未填写真实 Key 时，投标助手会使用 `stub` 客户端，工时拆分将回退到 NESMA 启发式，方便断网测试。

---

## 主要 API
所有接口前缀默认为 `/api`。

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| Auth | POST | `/api/auth/register` | 注册新账号 |
| Auth | POST | `/api/auth/login` | 登录获取 JWT |
| Auth | GET  | `/api/auth/me` | 获取当前用户信息 |
| Bidding | POST | `/api/bidding/analyze/text` | 粘贴文本触发标书分析 |
| Bidding | POST | `/api/bidding/analyze/file` | 上传文件分析（支持 async 模式） |
| Bidding | GET  | `/api/bidding/jobs` | 查看当前用户的分析任务 |
| Bidding | GET  | `/api/bidding/jobs/{job_id}` | 查看任务详情 |
| Workload | POST | `/api/workload/analyze` | 上传 Excel，输出人月拆分结果 |
| Workload | POST | `/api/workload/export` | 导出拆分结果为 Excel |
| Costing | POST | `/api/costing/analyze` | 上传 Excel + 费率，生成成本估算 |

> 所有业务接口均要求 `Authorization: Bearer <token>` 请求头，投标任务记录也会按 `owner_id` 自动隔离。

---

## 前端使用指南
1. 首次访问 `/web/`，注册并登录账号。
2. 使用顶部 Tab 切换模块：
   - 投标助手：支持文本粘贴或文件上传，结果以 JSON 呈现（后续可引入更友好的视图）。
   - 工时拆分：上传 Excel（可多 Sheet），可选策略和人月上限。
   - 成本预估：上传同类 Excel，并填写各角色人月费率、架构师/项目经理系数。
3. 所有结果均以 JSON 展示，便于调试与对接；可在后续版本中增加导出/下载按钮。

---

## 后续规划
- **报销助手**：接入 OCR/规则校验，结合审批流与预算控制。
- **客户背调**：整合企业知识库或第三方 API（企查查等），形成客户画像卡片。
- **名词解释**：内置领域词典 + LLM 兜底，提升新手销售效率。
- **多模型交叉验证**：对工时与成本估算引入第二套模型策略，比较结果并给出可信区间/解释。
- **权限与审计**：扩展组织/团队维度，增加操作日志与数据加密策略。

欢迎基于此架构继续拓展模块，复用统一的认证、存储与前端壳。
