# Sales Assistant 部署手册

本文记录将项目部署到腾讯云 TencentOS Server (CentOS 系) 的完整流程，涵盖首次部署、证书申请、更新发布以及常见排障。

---

## 1. 前置准备

1. **域名解析**
   - 在域名服务商后台为 `saleassisstant.chat` 创建两条 `A` 记录：
     | 主机记录 | 类型 | 值 |
     | --- | --- | --- |
     | `@` | `A` | 43.142.131.208 |
     | `www` | `A` | 43.142.131.208 |
   - DNS 生效后可通过 `dig saleassisstant.chat +short` 验证。

2. **服务器登录**
   ```bash
   chmod 600 ~/.ssh/tencent.pem
   ssh -i ~/.ssh/tencent.pem root@43.142.131.208
   ```

3. **同步 `.env`**
   在本地配置好 `.env` 后复制到服务器：
   ```bash
   scp -i ~/.ssh/tencent.pem /path/to/.env root@43.142.131.208:/opt/sales-assistant/.env
   ```
   若首次部署尚未创建目录，可在部署完成后再复制。

---

## 2. 首次部署步骤

```bash
ssh -i ~/.ssh/tencent.pem root@43.142.131.208
git clone https://github.com/change8/SalesAssistant.git
cd SalesAssistant
sudo SA_DOMAIN=saleassisstant.chat SA_ADMIN_EMAIL=you@example.com ./deploy.sh
```

部署脚本将完成以下任务：

- 安装系统依赖：Git、Python3、pip、Nginx、Certbot、Firewalld。
- 创建系统用户 `salesassistant` 以及目录 `/opt/sales-assistant`。
- 克隆代码、创建虚拟环境、安装 Python 依赖。
- 拷贝 `.env.example` 到 `/opt/sales-assistant/.env`（若未存在）。
- 部署 systemd 服务 `sales-assistant.service` 并启动。
- 下发 Nginx 反向代理配置。
- 使用 Certbot 自动申请 `saleassisstant.chat` + `www.saleassisstant.chat` 的免费证书，并配置自动续期。

完成后访问 `https://saleassisstant.chat/health` 验证健康检查。

---

## 3. 更新与回滚

- **更新**：在服务器执行
  ```bash
  cd /opt/sales-assistant/app
  sudo ./update.sh
  ```
  或者在仓库执行 `git pull` 后手动运行 `sudo systemctl restart sales-assistant`.

- **回滚**：在 `/opt/sales-assistant/app` 内 `git checkout <commit>`，随后运行 `sudo ./update.sh`。

---

## 4. GitHub Actions 自动部署

仓库包含 `.github/workflows/deploy.yml`，在 push 到 `main` 时自动执行：

1. **设置 Secrets**
   - `DEPLOY_HOST`：`43.142.131.208`
   - `DEPLOY_USER`：`root`（或自定义非 root 用户）
   - `DEPLOY_KEY`：服务器私钥内容（PEM）
   - `DEPLOY_PORT`：(可选) 非默认 22 端口

2. **流程内容**：连接服务器后执行 `/opt/sales-assistant/app/update.sh`。

---

## 5. 微信小程序配置

| 项目 | 值 |
| --- | --- |
| AppID | `wxa7a547d84de3f72a` |
| 请求域名 | `https://saleassisstant.chat` |
| 上传域名 | `https://saleassisstant.chat` |
| WebSocket | 暂未使用 |

在微信公众平台 → 开发 → 开发设置中配置 `request合法域名`、`uploadFile合法域名`、`downloadFile合法域名` 均为 `https://saleassisstant.chat`。  
因微信强制 HTTPS，需确保证书申请成功且处于有效期。

小程序端配置建议集中在 `frontend/miniapp/config.js`，设置：
```javascript
module.exports = {
  apiBaseUrl: 'https://saleassisstant.chat/api',
};
```

---

## 6. 调试与排障

- **查看服务状态**
  ```bash
  sudo systemctl status sales-assistant
  sudo journalctl -u sales-assistant -n 200 --no-pager
  ```
- **查看 Nginx 日志**
  ```bash
  sudo tail -f /var/log/nginx/sales-assistant.error.log
  ```
- **证书续期检查**
  ```bash
  sudo certbot renew --dry-run
  ```
- **任务模块自检**
  - 浏览器访问 `https://saleassisstant.chat/health`
  - 登录后通过“任务中心”验证轮询是否正常

---

## 7. 数据备份建议

- SQLite：定期备份 `/opt/sales-assistant/sales_assistant.db`。
- 证书：`/etc/letsencrypt/live/saleassisstant.chat/`。
- 日志：`/opt/sales-assistant/logs/*.log` + `/var/log/nginx/`。

可使用 `cron` 或云厂商备份脚本进行增量备份。

---

## 8. 常见问题

| 问题 | 解决方案 |
| --- | --- |
| `python3` 版本过低 | 安装 IUS 仓库或使用 `pyenv` 安装 3.10+，更新 `deploy.sh` 的 `PYTHON_BIN`。 |
| `certbot` 失败 | 确认域名已解析到服务器；关闭 80/443 上的其他服务；重试 `certbot --nginx`。 |
| 上传大文件失败 | 在 `ops/nginx/sales-assistant.template.conf` 中调整 `client_max_body_size`，重新部署。 |
| 任务卡在 pending | 检查 `.env` 中的大模型 Key 是否正确；查看后端日志排错。 |

---

如需切换 PostgreSQL/MySQL，请参考 README 中的高级部署章节或与团队运维协作，修改 `.env` 中的 `SA_DATABASE_URL` 即可。***
