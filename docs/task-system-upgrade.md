# 任务系统升级说明

> 更新日期：2025-10-21

本文档说明新的任务系统架构、特性和使用方法。

---

## 🎯 升级目标

本次升级解决了以下关键问题：

1. ✅ **稳定性问题**：增强了LLM调用的重试机制，使用指数退避策略
2. ✅ **任务持久化**：所有任务现在存储在数据库中，服务重启不会丢失
3. ✅ **日志增强**：结构化日志记录所有LLM请求/响应/耗时/错误
4. ✅ **任务队列**：基于数据库的轻量级任务队列，无需额外依赖

---

## 🏗️ 新架构概览

### 组件构成

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Frontend      │      │   FastAPI        │      │   Database      │
│                 │─────▶│   /api/tasks     │◀────▶│   tasks 表      │
│                 │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │                          ▲
                                  │                          │
                                  ▼                          │
                         ┌──────────────────┐               │
                         │   Task Worker    │───────────────┘
                         │   (后台进程)      │
                         │                  │
                         │  - 轮询任务      │
                         │  - 执行LLM调用  │
                         │  - 更新状态      │
                         │  - 处理重试      │
                         └──────────────────┘
```

### 数据流

```
用户上传文件
    ↓
API创建Task (status=PENDING)
    ↓
立即返回task_id给用户
    ↓
Worker轮询到任务
    ↓
更新status=RUNNING
    ↓
执行LLM调用（带重试）
    ↓
成功: status=COMPLETED + result
失败: status=RETRY (可重试) 或 FAILED (重试次数耗尽)
    ↓
前端轮询/api/tasks/{task_id}获取结果
```

---

## 📋 核心功能

### 1. 任务持久化

所有任务存储在 `tasks` 表中，包含：

- **基础信息**：task_type, status, user_id
- **输入数据**：payload (JSON)
- **执行状态**：retry_count, started_at, completed_at
- **输出结果**：result (JSON), error
- **元数据**：metadata (调试信息、耗时等)

**状态流转**：

```
PENDING → RUNNING → COMPLETED
                  ↓
                FAILED → RETRY → RUNNING → ...
                       ↓
                   CANCELLED
```

### 2. 增强的重试机制

使用 `tenacity` 库实现智能重试：

- **重试条件**：网络超时、5xx错误、连接错误
- **重试策略**：指数退避 (2s → 4s → 8s → ...)
- **最大重试次数**：默认3次（可配置）
- **不重试的错误**：4xx错误、JSON解析失败（第二次后）

**代码位置**：
- `backend/app/common/llm_retry.py` - 重试装饰器
- `BiddingAssistant/backend/analyzer/llm_enhanced.py` - 增强的LLM客户端
- `SplitWorkload/backend/app/core/llm_client_enhanced.py` - 工时分析LLM客户端

### 3. 结构化日志

所有LLM调用都会记录：

```json
{
  "event": "llm_request",
  "provider": "dashscope",
  "model": "qwen3-max",
  "prompt_tokens": 1234,
  "timestamp": "2025-10-21T10:30:00Z"
}

{
  "event": "llm_response",
  "provider": "dashscope",
  "model": "qwen3-max",
  "duration_ms": 2345.67,
  "success": true,
  "response_tokens": 567
}
```

**失败日志示例**：

```json
{
  "event": "llm_response",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "duration_ms": 90123.45,
  "success": false,
  "error": "Timeout after 90s"
}
```

### 4. 轻量级任务队列

基于数据库轮询的任务队列：

- **无额外依赖**：不需要Redis、RabbitMQ等
- **持久化**：任务存储在SQLite/PostgreSQL
- **可扩展**：未来可平滑迁移到Celery
- **简单可靠**：适合中小规模（<1000任务/小时）

**Worker配置**：

```python
TaskWorker(
    poll_interval=2.0,      # 每2秒轮询一次
    batch_size=5,           # 每次处理最多5个任务
    max_consecutive_errors=10  # 连续失败10次后停止
)
```

---

## 🚀 使用指南

### 安装依赖

```bash
# 安装新增依赖
pip install -r backend/requirements.txt
```

新增依赖：
- `tenacity==8.2.3` - 重试机制

### 数据库迁移

```bash
# 创建/更新数据库表
python backend/migrate_db.py
```

这将创建 `tasks` 表。

### 启动服务

#### 1. 启动主API服务

```bash
./start_backend.sh
```

#### 2. 启动任务Worker（新增）

**重要：必须在单独的终端启动worker**

```bash
./start_worker.sh
```

Worker会：
- 每2秒轮询数据库
- 执行待处理任务
- 自动重试失败任务
- 记录详细日志

**生产环境建议**：
- 使用 `supervisor` 或 `systemd` 管理worker进程
- 配置自动重启
- 设置日志轮转

### API使用示例

#### 创建标书分析任务（文本）

```bash
curl -X POST "http://localhost:8000/api/tasks/bidding/text" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "text=这里是标书内容..." \
  -F "max_retries=3"
```

返回：

```json
{
  "id": 123,
  "task_type": "bidding_analysis",
  "status": "pending",
  "retry_count": 0,
  "max_retries": 3,
  "created_at": "2025-10-21T10:30:00Z",
  "metadata": {"source": "text"}
}
```

#### 创建标书分析任务（文件）

```bash
curl -X POST "http://localhost:8000/api/tasks/bidding/file" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@tender.pdf" \
  -F "max_retries=3"
```

#### 查询任务状态和结果

```bash
curl "http://localhost:8000/api/tasks/123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**任务进行中**：

```json
{
  "id": 123,
  "status": "running",
  "started_at": "2025-10-21T10:30:05Z",
  "result": null
}
```

**任务完成**：

```json
{
  "id": 123,
  "status": "completed",
  "started_at": "2025-10-21T10:30:05Z",
  "completed_at": "2025-10-21T10:31:23Z",
  "result": {
    "summary": "本项目为...",
    "tabs": [...]
  },
  "metadata": {
    "duration_ms": 78234.56
  }
}
```

**任务失败（可重试）**：

```json
{
  "id": 123,
  "status": "retry",
  "retry_count": 1,
  "max_retries": 3,
  "error": "LLM 请求超时，请检查网络或稍后再试"
}
```

**任务失败（重试耗尽）**：

```json
{
  "id": 123,
  "status": "failed",
  "retry_count": 3,
  "max_retries": 3,
  "error": "LLM 请求超时，请检查网络或稍后再试",
  "metadata": {
    "retry_exhausted": true
  }
}
```

#### 列出用户所有任务

```bash
curl "http://localhost:8000/api/tasks?limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 获取任务统计

```bash
curl "http://localhost:8000/api/tasks/stats" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

返回：

```json
{
  "stats": {
    "pending": 2,
    "running": 1,
    "completed": 15,
    "failed": 1,
    "retry": 0,
    "cancelled": 0
  }
}
```

#### 取消任务

```bash
curl -X DELETE "http://localhost:8000/api/tasks/123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## ⚙️ 配置选项

### 环境变量

```bash
# LLM超时配置（秒，0=无限等待）
BIDDING_ASSISTANT_LLM_TIMEOUT=90
SPLITWORKLOAD_MODEL_TIMEOUT=60

# Worker配置（可选，在代码中修改）
# 见 backend/app/tasks/worker.py
```

### 超时建议

不同LLM的推荐超时：

| Provider | 任务类型 | 推荐超时 |
|----------|---------|---------|
| OpenAI | 标书分析 | 90秒 |
| DashScope | 工时拆分 | 60秒 |
| Azure OpenAI | 标书分析 | 120秒 |

**注意**：
- 超时设置为0会无限等待（不推荐）
- 超时过短会导致频繁失败
- 超时过长会阻塞worker

---

## 🐛 故障排查

### Worker无法启动

**问题**：`ModuleNotFoundError: No module named 'backend'`

**解决**：

```bash
export PYTHONPATH=/home/user/SalesAssistant:$PYTHONPATH
python -m backend.app.tasks.worker
```

### 任务一直PENDING

**可能原因**：
1. Worker未启动
2. Worker已崩溃

**检查**：

```bash
# 查看worker日志
tail -f worker.log

# 手动运行worker查看错误
python -m backend.app.tasks.worker
```

### 任务频繁失败

**可能原因**：
1. LLM API Key无效
2. 网络问题
3. 超时设置过短

**检查日志**：

```bash
# 查看详细错误
curl "http://localhost:8000/api/tasks/123"

# 查看worker日志
grep "task_id=123" worker.log
```

### LLM调用超时

**优化方案**：
1. 增加超时时间（建议90-120秒）
2. 检查网络连接
3. 使用备用LLM provider

---

## 📊 监控建议

### 关键指标

1. **任务成功率**：
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as success_rate
   FROM tasks
   WHERE created_at > NOW() - INTERVAL '1 day';
   ```

2. **平均处理时长**：
   ```sql
   SELECT
     task_type,
     AVG((completed_at - started_at)) as avg_duration
   FROM tasks
   WHERE status = 'completed'
   GROUP BY task_type;
   ```

3. **重试次数分布**：
   ```sql
   SELECT
     retry_count,
     COUNT(*) as count
   FROM tasks
   GROUP BY retry_count
   ORDER BY retry_count;
   ```

### 告警规则

建议设置告警：
- 任务失败率 > 10%
- 平均处理时长 > 2分钟
- Worker停止响应
- 待处理任务堆积 > 50个

---

## 🔄 从旧系统迁移

### 兼容性说明

旧的 `/api/bidding/analyze/file` 等端点仍然可用（暂未移除），但建议迁移到新的任务API。

### 迁移步骤

1. **前端改造**：
   - 从同步调用改为异步（创建任务 → 轮询状态）
   - 添加任务列表页面
   - 添加重试/取消按钮

2. **数据迁移**：
   - 旧的内存任务无需迁移（重启后丢失）
   - 新系统从空数据库开始

3. **渐进式切换**：
   - 可以同时运行新旧系统
   - 逐步将流量切换到新API

---

## 🚧 后续优化计划

### 短期（1-2周）

- [ ] 前端适配新任务API
- [ ] 添加任务进度推送（WebSocket）
- [ ] 优化prompt（单独文档）

### 中期（1个月）

- [ ] 引入Alembic数据库迁移
- [ ] 添加任务优先级
- [ ] 实现任务批量处理

### 长期（3个月）

- [ ] 评估迁移到Celery（如需要）
- [ ] 多LLM provider负载均衡
- [ ] 完善监控和告警系统

---

## 📚 相关文档

- [架构总览](architecture-overview.md)
- [TODO列表](todo.md)
- [LLM Provider配置](.env.example)

---

## 💬 反馈和支持

如有问题或建议，请在项目issue中反馈。
