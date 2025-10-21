# 🚀 任务系统升级快速开始

本指南帮你快速启动升级后的系统。详细文档见 [docs/task-system-upgrade.md](docs/task-system-upgrade.md)

---

## ⚡ 3步快速启动

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 2. 运行数据库迁移

```bash
python backend/migrate_db.py
```

### 3. 启动服务（两个终端）

**终端1 - API服务**：
```bash
./start_backend.sh
```

**终端2 - 任务Worker**：
```bash
./start_worker.sh
```

✅ 完成！访问 http://localhost:8000/web/

---

## 🎯 核心改进

| 改进项 | 说明 |
|-------|------|
| ✅ 增强重试 | 网络错误/超时自动重试3次，指数退避 |
| ✅ 任务持久化 | 所有任务存数据库，重启不丢失 |
| ✅ 结构化日志 | 记录所有LLM请求/响应/耗时/错误 |
| ✅ 任务队列 | 基于数据库轮询，无需Redis |

---

## 📋 新的API端点

### 创建任务（替代旧的同步API）

```bash
# 文本分析
curl -X POST "http://localhost:8000/api/tasks/bidding/text" \
  -H "Authorization: Bearer $TOKEN" \
  -F "text=标书内容..."

# 文件分析
curl -X POST "http://localhost:8000/api/tasks/bidding/file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@tender.pdf"
```

返回：
```json
{
  "id": 123,
  "task_type": "bidding_analysis",
  "status": "pending",
  "created_at": "2025-10-21T10:30:00Z"
}
```

### 查询任务状态

```bash
curl "http://localhost:8000/api/tasks/123" \
  -H "Authorization: Bearer $TOKEN"
```

**进行中**：
```json
{"status": "running", "result": null}
```

**已完成**：
```json
{
  "status": "completed",
  "result": {
    "summary": "...",
    "tabs": [...]
  }
}
```

### 列出所有任务

```bash
curl "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚙️ 配置要点

### .env 超时配置

```bash
# 推荐超时设置（秒）
BIDDING_ASSISTANT_LLM_TIMEOUT=90  # 标书分析
SPLITWORKLOAD_MODEL_TIMEOUT=60    # 工时拆分
```

⚠️ **不要设置为0**（无限等待会导致worker阻塞）

---

## 🐛 快速排查

### Worker未启动导致任务卡在PENDING？

检查worker是否运行：
```bash
ps aux | grep "backend.app.tasks.worker"
```

启动worker：
```bash
./start_worker.sh
```

### 任务频繁失败？

查看详细错误：
```bash
curl "http://localhost:8000/api/tasks/123" -H "Authorization: Bearer $TOKEN"
```

检查LLM配置：
```bash
# 确保.env中配置了有效的API Key
cat .env | grep API_KEY
```

---

## 📊 监控建议

```bash
# 查看任务统计
curl "http://localhost:8000/api/tasks/stats" -H "Authorization: Bearer $TOKEN"
```

返回：
```json
{
  "stats": {
    "pending": 2,
    "running": 1,
    "completed": 15,
    "failed": 1
  }
}
```

---

## 🎓 下一步

1. **前端适配**：修改前端使用新的异步任务API
2. **Prompt优化**：讨论如何改进LLM输出质量（等你回来讨论）
3. **监控部署**：添加任务成功率、耗时监控

---

## 📚 详细文档

- [完整升级文档](docs/task-system-upgrade.md)
- [架构说明](docs/architecture-overview.md)
- [API参考](http://localhost:8000/docs)

有问题随时问！
