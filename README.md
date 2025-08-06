# CalDAV 同步工具 v3

一个功能完整的 Python CalDAV 同步工具，支持多账号管理、事件同步、文件合并和 GitHub Actions 自动化部署。

## 🚀 项目特性

- 🔧 **统一配置管理**: 使用 `.env` 文件集中管理所有账号信息
- 🏗️ **模块化架构**: 每个 CalDAV 服务都有独立的同步处理器
- 📅 **多服务支持**: 支持钉钉日历和腾讯会议日历
- 🎯 **灵活同步**: 支持按类型、按名称或全部同步，并可自定义同步时间范围。
- 📁 **自动组织**: 自动创建目录结构并保存 ICS 文件
- 🔄 **文件合并**: 支持按账号类型合并和全局合并 ICS 文件
- 🗂️ **临时文件管理**: XML 临时文件统一存放和自动清理
- 🤖 **GitHub Actions 自动化**: 支持定时同步和自动部署到 GitHub Pages
- 🌐 **GitHub Pages 集成**: 自动生成美观的日历文件下载页面
- 🐛 **调试友好**: 完整的 VSCode 调试配置

## 📁 项目结构

```
sync-caldav-v3/
├── .env                    # 环境配置文件
├── config_manager.py       # 配置管理模块
├── main.py                 # 主程序入口
├── sync_dingtalk.py        # 钉钉同步处理器
├── sync_tencent.py         # 腾讯会议同步处理器
├── ics_merger.py           # ICS文件合并工具
├── requirements.txt        # 依赖包列表
├── temp/                   # XML临时文件目录
├── public/                 # 所有合并后的ICS文件
├── {service}_events_{user}/# 各服务的事件目录
├── .vscode/               # VSCode 调试配置
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
└── README.md              # 项目文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置账号

复制 `.env.example` 为 `.env` 并填入你的账号信息：

```env
# 全局设置
OUTPUT_DIR=calendar_events
TIMEOUT=30

# 钉钉账号配置
DINGTALK_ACCOUNT_NAME=钉钉日历账号
DINGTALK_USERNAME=your_dingtalk_username
DINGTALK_PASSWORD=your_dingtalk_password
DINGTALK_URL=https://calendar.dingtalk.com/dav/{username}/

# 腾讯会议账号配置
TENCENT_ACCOUNT_NAME=腾讯会议账号
TENCENT_USERNAME=your_tencent_username
TENCENT_PASSWORD=your_tencent_password
TENCENT_URL=https://cal.meeting.tencent.com/caldav/{username}/calendar/
```

### 3. 使用方法

#### 基础同步功能
```bash
# 查看帮助
python main.py --help

# 列出所有配置的账号
python main.py --list

# 同步所有账号
python main.py --sync-all

# 按类型同步
python main.py --sync-type dingtalk
python main.py --sync-type tencent

# 按名称同步
python main.py --sync-name "钉钉日历账号"
```

#### 文件合并功能
```bash
# 按类型合并ICS文件
python main.py --merge-type dingtalk
python main.py --merge-type tencent

# 合并所有账号的ICS文件
python main.py --merge-all
```

#### 维护功能
```bash
# 清理临时文件（默认7天前）
python main.py --cleanup

# 清理指定天数前的临时文件
python main.py --cleanup 3
```

#### 完整工作流程
```bash
# 一键运行完整工作流程（推荐）
python main.py --workflow

# 自定义清理天数的完整工作流程
python main.py --workflow 3
```

## 🤖 GitHub Actions 自动化

### 快速开始

1. **Fork 或克隆项目到你的 GitHub 仓库**

2. **配置 GitHub Secrets**：
   - 进入仓库 Settings → Secrets and variables → Actions
   - 添加以下 Secrets：
     ```
     DINGTALK_ACCOUNT_NAME=钉钉日历账号
     DINGTALK_USERNAME=your_dingtalk_username
     DINGTALK_PASSWORD=your_dingtalk_password
     DINGTALK_URL=https://calendar.dingtalk.com/dav/{username}/

     TENCENT_ACCOUNT_NAME=腾讯会议账号
     TENCENT_USERNAME=your_tencent_username
     TENCENT_PASSWORD=your_tencent_password
     TENCENT_URL=https://cal.meeting.tencent.com/caldav/{username}/calendar/
     ```

3. **启用 GitHub Pages**：
   - 进入仓库 Settings → Pages
   - Source 选择 "GitHub Actions"

4. **运行工作流**：
   - 进入 Actions 标签
   - 选择 "CalDAV 同步和 GitHub Pages 部署"
   - 点击 "Run workflow"

### 自动化功能

- **⏰ 定时同步**：每天 8:00 和 20:00（北京时间）自动运行
- **🔄 手动触发**：支持按需同步特定服务或全部服务
- **🌐 自动部署**：同步完成后自动部署到 GitHub Pages
- **🧹 自动清理**：自动清理过期的临时文件
- **📊 状态监控**：工作流执行状态和结果通知

### 工作流说明

| 工作流文件 | 功能 | 触发条件 |
|-----------|------|----------|
| `sync-and-deploy.yml` | 完整同步和部署 | 定时/手动/推送 |
| `deploy-only.yml` | 仅部署现有文件 | 手动触发 |
| `pages.yml` | GitHub Pages 构建 | 文件变更/手动 |

详细配置说明请参考：[GitHub Actions 设置指南](GITHUB_SETUP.md)

## 🏗️ 架构说明

### 配置管理 (config_manager.py)

- **CalDAVAccount**: 数据类，表示单个 CalDAV 账号
- **ConfigManager**: 配置管理器，负责解析 `.env` 文件和管理账号配置

```python
@dataclass
class CalDAVAccount:
    account_type: str
    account_name: str
    username: str
    password: str
    url: str

    def get_formatted_url(self) -> str:
        return self.url.format(username=self.username)
```

### 主程序 (main.py)

- **CalDAVSyncManager**: 主同步管理器
- 提供统一的命令行接口
- 支持多种同步模式和合并功能

### 同步处理器

#### 钉钉同步 (sync_dingtalk.py)
- **DingTalkCalDAVSync**: 钉钉 CalDAV 同步处理器
- 使用 REPORT 方法获取事件数据
- 支持时间范围过滤

#### 腾讯会议同步 (sync_tencent.py)
- **TencentCalDAVSync**: 腾讯会议 CalDAV 同步处理器
- 两步同步：PROPFIND 获取事件列表 + calendar-multiget 获取事件内容
- 处理相对路径 URL

### ICS合并工具 (ics_merger.py)

- **ICSMerger**: ICS 文件合并处理器
- 支持按账号类型合并和全局合并
- 自动处理时区信息和事件去重
- 临时文件统一管理

## 📂 输出结构

### 事件文件结构
```
{service}_events_{username}/
└── {calendar_name}/
    ├── 20250806_100153_1_event_title.ics
    ├── 20250806_100153_2_event_title.ics
    └── ...
```

### 合并文件结构
```
public/                     # 所有合并后的ICS文件
├── all_calendars_latest.ics
├── dingtalk_latest.ics
└── tencent_latest.ics

temp/                       # 临时XML文件
├── dingtalk_collections_username.xml
├── dingtalk_events_username_primary.xml
├── tencent_collections_username.xml
└── tencent_events_username_calendar.xml
```

## 🔧 调试配置

项目包含完整的 VSCode 调试配置：

- **主程序调试**: 调试 main.py 的各种参数组合
- **钉钉同步调试**: 单独调试钉钉同步功能
- **腾讯会议同步调试**: 单独调试腾讯会议同步功能
- **合并工具调试**: 调试 ICS 文件合并功能

## 🛠️ 技术实现

### CalDAV 协议支持

- **PROPFIND**: 发现日历集合和事件列表
- **REPORT**: 查询事件数据（钉钉使用 calendar-query）
- **calendar-multiget**: 批量获取事件内容（腾讯会议使用）

### ICS 文件处理

- 标准 ICS (iCalendar) 格式支持
- 自动解析 VEVENT 和 VTIMEZONE 组件
- 智能合并和去重处理
- 安全的文件名生成

### 错误处理

- 网络连接异常处理
- XML 解析错误处理
- 账号认证失败处理
- 文件写入异常处理

## 📦 依赖包

- `requests`: HTTP 请求库
- `python-dotenv`: 环境变量管理
- `xml.etree.ElementTree`: XML 解析（内置）
- `dataclasses`: 数据类支持（内置）
- `re`: 正则表达式（内置）
- `glob`: 文件模式匹配（内置）

## 📋 使用示例

### 完整工作流程

```bash
# 1. 同步所有账号
python main.py --sync-all

# 2. 按类型合并文件
python main.py --merge-type dingtalk
python main.py --merge-type tencent

# 3. 创建全局合并文件
python main.py --merge-all

# 4. 清理临时文件
python main.py --cleanup
```

### 单独使用合并工具

```bash
# 直接运行合并工具
python ics_merger.py
```

## 🌐 GitHub Pages 部署

项目支持自动部署到 GitHub Pages，提供美观的日历文件下载界面。

### 访问地址
- **GitHub Pages URL**: `https://your-username.github.io/sync-caldav-v3/`
- **自动更新**: 每次同步完成后自动更新页面内容

### 页面功能
- 📋 **统一文件列表**: 在一个页面中显示所有合并后的日历文件。
- 📊 **文件信息**: 清晰展示文件大小、修改时间等详细信息。
- 🎨 **响应式设计**: 自动适应桌面和移动设备访问。
- 🔄 **动态加载**: 通过 `files.json` 动态加载文件列表，确保信息最新。

### 文件组织
所有合并后的文件都位于 `public` 目录，并可通过 `ICS_FILE_NAME` 变量控制文件名后缀。
- **全局合并文件**: `all_calendars_[ICS_FILE_NAME].ics`
- **按类型合并**: `dingtalk_[ICS_FILE_NAME].ics`, `tencent_[ICS_FILE_NAME].ics`
- **直接下载**: 点击文件名即可下载到本地。

## 📈 版本历史

### v3.2.0 (当前版本)
- 🤖 **新增 GitHub Actions 自动化支持**
- 🌐 **集成 GitHub Pages 自动部署**
- ⏰ **支持定时同步**（每天 8:00 和 20:00）
- 🎨 **美观的 Web 界面**，支持响应式设计
- 📊 **动态文件列表**，自动检测生成的文件
- 🔧 **完善的配置管理**，支持 GitHub Secrets
- 📚 **详细的部署文档**和设置指南

### v3.1.0
- 新增 ICS 文件合并功能
- 添加按账号类型合并支持
- 实现全局合并功能
- 统一 XML 临时文件管理
- 添加临时文件自动清理
- 完善命令行界面

### v3.0.0
- 重构为统一架构
- 添加 `.env` 配置文件支持
- 实现模块化同步处理器
- 添加命令行界面
- 完善调试配置

### v2.0.0
- 支持腾讯会议 CalDAV
- 实现 calendar-multiget 方法
- 优化事件解析逻辑

### v1.0.0
- 基础钉钉 CalDAV 支持
- ICS 文件生成功能

## 🔍 故障排除

### 常见问题

1. **认证失败**: 检查用户名和密码是否正确
2. **网络连接超时**: 调整 `TIMEOUT` 配置或检查网络连接
3. **XML 解析错误**: 检查服务器响应格式是否正确
4. **文件权限错误**: 确保有写入权限
5. **合并失败**: 检查 ICS 文件是否存在和格式是否正确

### 调试技巧

1. 使用 `--verbose` 参数获取详细输出
2. 检查 `temp/` 目录中的 XML 响应文件
3. 使用 VSCode 调试器逐步执行
4. 查看网络请求和响应内容
5. 检查合并后的 ICS 文件格式

### 性能优化

- 定期清理临时文件：`python main.py --cleanup`
- 按需同步特定账号类型
- 使用合并功能减少文件数量

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请创建 Issue 或联系项目维护者。

---

**CalDAV 同步工具 v3** - 让多平台日历同步变得简单高效！
