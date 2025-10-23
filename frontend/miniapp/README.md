# 微信小程序端使用说明

## 1. 准备配置

复制模板文件为实际配置：

```bash
cp frontend/miniapp/config.js.sample frontend/miniapp/config.js
```

将 `apiBaseUrl` 修改为部署在服务器上的域名，例如：

```js
module.exports = {
  apiBaseUrl: 'https://saleassisstant.chat/api'
};
```

## 2. 导入微信开发者工具

1. 打开微信开发者工具，选择 “导入项目”。
2. AppID 填写 `wxa7a547d84de3f72a`。
3. 项目目录选择仓库中的 `frontend/miniapp`。
4. 勾选 “不使用云开发”，确认导入。

## 3. 域名配置

在微信公众平台 → 开发 → 开发设置：

- request 合法域名：`https://saleassisstant.chat`
- uploadFile 合法域名：`https://saleassisstant.chat`
- downloadFile 合法域名：`https://saleassisstant.chat`

确保该域名已备案并部署 HTTPS（部署脚本已通过 Certbot 获取证书）。

## 4. 运行 / 上传

在微信开发者工具中：

- 选择 “预览” 可扫码让手机体验。
- 选择 “上传” 提交审核。上传时请填写版本号和备注。

## 5. 功能说明

- 登录：输入手机号和密码，成功后自动保存 Token。
- 标书分析：上传 PDF/Word/TXT 文件，系统自动创建任务并轮询结果。
- 工时拆分、成本估算：上传 Excel，创建后台任务，结果可在任务页查看。
- 任务队列：查看最近任务状态，失败任务会展示错误信息。

> 若需要清除登录状态，可在微信开发者工具的模拟器中点击 “清缓存”。

