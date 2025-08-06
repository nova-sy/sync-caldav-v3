# GitHub Actions 和 GitHub Pages 设置指南

本文档详细说明如何为 CalDAV 同步工具配置 GitHub Actions 自动化和 GitHub Pages 部署。

## 📋 前置要求

1. GitHub 仓库（公开或私有均可）
2. 钉钉和腾讯会议的 CalDAV 账号信息
3. GitHub Pages 功能已启用

## 🔧 第一步：配置 GitHub Secrets

在 GitHub 仓库中配置以下 Secrets（Settings → Secrets and variables → Actions）：

### 必需的 Secrets

| Secret 名称 | 描述 | 示例值 |
|------------|------|--------|
| `DINGTALK_ACCOUNT_NAME` | 钉钉账号显示名称 | `钉钉日历账号` |
| `DINGTALK_USERNAME` | 钉钉用户名 | `your_dingtalk_username` |
| `DINGTALK_PASSWORD` | 钉钉密码 | `your_dingtalk_password` |
| `DINGTALK_URL` | 钉钉 CalDAV URL | `https://calendar.dingtalk.com/dav/{username}/` |
| `TENCENT_ACCOUNT_NAME` | 腾讯会议账号显示名称 | `腾讯会议账号` |
| `TENCENT_USERNAME` | 腾讯会议用户名 | `your_tencent_username` |
| `TENCENT_PASSWORD` | 腾讯会议密码 | `your_tencent_password` |
| `TENCENT_URL` | 腾讯会议 CalDAV URL | `https://cal.meeting.tencent.com/caldav/{username}/calendar/` |

### 设置步骤

1. 进入 GitHub 仓库页面
2. 点击 **Settings** 标签
3. 在左侧菜单中选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 输入 Secret 名称和值
6. 点击 **Add secret**
7. 重复以上步骤添加所有必需的 Secrets

## 🌐 第二步：启用 GitHub Pages

### 方法一：通过仓库设置启用

1. 进入 GitHub 仓库页面
2. 点击 **Settings** 标签
3. 在左侧菜单中选择 **Pages**
4. 在 **Source** 部分选择 **GitHub Actions**
5. 保存设置

### 方法二：通过工作流自动启用

GitHub Actions 工作流会自动配置 GitHub Pages，无需手动设置。

## 🚀 第三步：工作流说明

项目包含三个主要的 GitHub Actions 工作流：

### 1. 主工作流：`sync-and-deploy.yml`

**功能**：完整的同步和部署流程
- 同步钉钉和腾讯会议日历
- 合并 ICS 文件
- 部署到 GitHub Pages

**触发条件**：
- 定时执行：每天 8:00 和 20:00（北京时间）
- 手动触发：支持选择同步类型和清理天数
- 代码推送：推送到 main 分支时（仅用于测试）

**手动触发参数**：
- `sync_type`: 同步类型（all/dingtalk/tencent）
- `cleanup_days`: 清理多少天前的临时文件（默认 7 天）

### 2. 仅部署工作流：`deploy-only.yml`

**功能**：仅部署现有文件到 GitHub Pages
- 不执行同步操作
- 直接部署 public 和 merged 目录的内容

**触发条件**：
- 手动触发

**使用场景**：
- 修改了页面样式需要重新部署
- 同步失败但想部署现有文件
- 测试 GitHub Pages 配置

### 3. Pages 配置工作流：`pages.yml`

**功能**：专门的 GitHub Pages 构建和部署
- 生成动态文件列表
- 创建美观的索引页面
- 优化的页面加载体验

**触发条件**：
- public 或 merged 目录有变更时
- 手动触发

## 📁 第四步：目录结构说明

工作流运行后会生成以下目录结构：

```
项目根目录/
├── public/                          # 全局合并的日历文件
│   └── all_calendars_YYYYMMDD_HHMMSS.ics
├── merged/                          # 按类型合并的日历文件
│   ├── dingtalk_merged_YYYYMMDD_HHMMSS.ics
│   └── tencent_merged_YYYYMMDD_HHMMSS.ics
├── temp/                            # 临时 XML 文件（会被清理）
├── dingtalk_events_username/        # 钉钉事件文件
└── tencent_events_username/         # 腾讯会议事件文件
```

## 🎯 第五步：验证设置

### 检查 Secrets 配置

运行以下工作流来验证配置：

1. 进入 **Actions** 标签
2. 选择 **CalDAV 同步和 GitHub Pages 部署** 工作流
3. 点击 **Run workflow**
4. 选择 `sync_type: all`
5. 点击 **Run workflow**

### 检查执行日志

工作流运行时会输出详细日志：

```
=== 检查账号配置 ===
=== 已配置的 CalDAV 账号 ===
1. 钉钉日历账号
   类型: DINGTALK
   用户名: your_username
   URL: https://calendar.dingtalk.com/dav/your_username/

2. 腾讯会议账号
   类型: TENCENT
   用户名: your_username
   URL: https://cal.meeting.tencent.com/caldav/your_username/calendar/
```

### 检查 GitHub Pages

1. 工作流成功运行后，访问 GitHub Pages URL
2. URL 格式：`https://your-username.github.io/sync-caldav-v3/`
3. 页面应显示可下载的 ICS 文件列表

## 🔄 第六步：定时同步设置

工作流默认配置为每天两次自动同步：

- **上午 8:00**（北京时间）：`cron: '0 0 * * *'`
- **晚上 8:00**（北京时间）：`cron: '0 12 * * *'`

### 修改同步频率

编辑 `.github/workflows/sync-and-deploy.yml` 文件中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'    # 每天 UTC 00:00 (北京时间 08:00)
  - cron: '0 12 * * *'   # 每天 UTC 12:00 (北京时间 20:00)
```

**常用 cron 表达式**：
- 每小时：`'0 * * * *'`
- 每 6 小时：`'0 */6 * * *'`
- 每天一次：`'0 0 * * *'`
- 工作日每天：`'0 0 * * 1-5'`

## 🛠️ 故障排除

### 常见问题

1. **Secrets 未配置**
   - 错误：`KeyError: 'DINGTALK_USERNAME'`
   - 解决：检查所有必需的 Secrets 是否已正确配置

2. **认证失败**
   - 错误：`401 Unauthorized`
   - 解决：检查用户名和密码是否正确

3. **GitHub Pages 未启用**
   - 错误：`Error: Pages deployment failed`
   - 解决：在仓库设置中启用 GitHub Pages

4. **权限不足**
   - 错误：`Error: Resource not accessible by integration`
   - 解决：检查工作流的 permissions 配置

### 调试步骤

1. **查看工作流日志**：
   - Actions → 选择失败的工作流 → 查看详细日志

2. **测试本地配置**：
   ```bash
   # 创建本地 .env 文件
   cp .env.example .env
   # 编辑 .env 文件填入配置
   # 测试同步
   python main.py --list
   python main.py --sync-all
   ```

3. **手动触发工作流**：
   - 使用 `workflow_dispatch` 手动触发
   - 逐步测试各个功能

## 📊 监控和维护

### 工作流状态监控

1. **GitHub Actions 徽章**：
   ```markdown
   ![Sync Status](https://github.com/your-username/sync-caldav-v3/workflows/CalDAV%20同步和%20GitHub%20Pages%20部署/badge.svg)
   ```

2. **邮件通知**：
   - GitHub 会在工作流失败时发送邮件通知
   - 可在个人设置中配置通知偏好

### 定期维护

1. **清理临时文件**：工作流会自动清理 7 天前的临时文件
2. **更新依赖**：定期检查 `requirements.txt` 中的包版本
3. **监控存储使用**：GitHub Actions 有存储和运行时间限制

## 🔐 安全建议

1. **使用应用专用密码**：
   - 钉钉和腾讯会议建议使用应用专用密码而非主密码
   - 定期轮换密码

2. **最小权限原则**：
   - 工作流只请求必需的权限
   - 定期审查 Secrets 的使用

3. **监控访问日志**：
   - 定期检查 CalDAV 服务的访问日志
   - 发现异常访问及时处理

## 📞 获取帮助

如果遇到问题，可以：

1. 查看项目的 Issues 页面
2. 创建新的 Issue 描述问题
3. 提供详细的错误日志和配置信息

---

**注意**：请确保不要在代码中硬编码任何敏感信息，始终使用 GitHub Secrets 来存储账号信息。
