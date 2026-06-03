# Hermes 项目目录结构说明

## 项目概述
Hermes 是一个 AI Agent 框架，支持多种大模型接入、多种平台集成（Slack、Telegram、飞书等），提供完整的工具系统和插件机制。

---

## 核心模块

### `/agent`
**功能作用**：AI Agent 核心逻辑层
- 负责与各大模型（Anthropic、Gemini、OpenAI 等）通信
- 管理 Agent 的生命周期、上下文压缩、对话管理
- 实现各种适配器（Adapter）连接不同模型服务
- 包含 LSP（语言服务器协议）支持
- 处理传输层（Transports）通信

**关键子目录**：
- `lsp/` - 语言服务器协议实现
- `transports/` - 多种传输协议实现
- `secret_sources/` - 密钥来源管理（如 Bitwarden）

---

### `/acp_adapter`
**功能作用**：ACP（Agent Communication Protocol）适配器
- 提供 ACP 协议的服务端实现
- 管理认证、会话、事件处理
- 权限控制和审批流程

---

### `/acp_registry`
**功能作用**：ACP 注册表
- 存放 Agent 的元数据配置
- 包含 Agent 的图标和定义文件

---

### `/gateway`
**功能作用**：消息网关核心
- 管理所有平台的消息收发
- 实现跨平台的消息路由和分发
- 支持的平台：Slack、Telegram、飞书、WhatsApp、企业微信、钉钉、Signal、Matrix、邮件等

**关键子目录**：
- `platforms/` - 各个平台的具体实现

---

### `/hermes_cli`
**功能作用**：Hermes 命令行工具
- 提供 `hermes` 终端命令
- 包含配置管理、认证、部署等功能
- TUI 界面支持

---

### `/tools`
**功能作用**：工具系统
- 包含 Agent 可调用的各种工具实现
- 文件操作、终端执行、浏览器控制
- 第三方服务集成（飞书文档、云文档、GitHub 等）
- MCP（Model Context Protocol）工具支持

**关键子目录**：
- `computer_use/` - 计算机使用能力（CUA）
- `environments/` - 多种执行环境（Docker、SSH、Modal 等）

---

### `/plugins`
**功能作用**：插件系统
- 提供可扩展的插件机制
- 内置插件：Spotify、Teams Pipeline、Google Meet、安全指导、记忆系统等

---

### `/tui_gateway`
**功能作用**：TUI 网关
- 提供终端用户界面的网关实现
- WebSocket 传输支持

---

## 平台与集成

### `/providers`
**功能作用**：AI 模型提供商
- 基础 Provider 接口定义
- 支持多种大模型服务

---

### `/platforms` (在 `/gateway` 下)
**功能作用**：消息平台集成
支持的平台：
- **即时通讯**：Slack、Telegram、飞书、WhatsApp、Signal、Matrix、钉钉、企业微信
- **办公协作**：飞书（文档、评论）、Microsoft Teams
- **其他**：邮件、短信、Webhook、家庭助理（HomeAssistant）

---

## 前端相关

### `/ui-tui`
**功能作用**：终端 UI 项目
- 使用 TypeScript 开发
- 提供 TUI 界面组件

### `/web`
**功能作用**：Web 前端项目
- 入口 HTML 和前端资源

### `/website`
**功能作用**：文档网站
- 使用 Docusaurus 构建
- 包含用户文档和使用案例

---

## 开发与部署

### `/docker`
**功能作用**：Docker 容器化配置
- 多阶段构建支持
- 容器初始化脚本

### `/nix`
**功能作用**：Nix 包管理配置
- NixOS 模块定义
- 开发环境配置

### `/scripts`
**功能作用**：实用脚本
- 安装脚本（install.sh、install.ps1）
- 测试和分析工具
- 发布和构建脚本

---

## 数据与配置

### `/locales`
**功能作用**：国际化资源
- 包含 16 种语言的翻译文件
- 支持：中文（简体/繁体）、英文、日语、韩语、法语、德语等

### `/cron`
**功能作用**：定时任务系统
- 作业调度器实现
- 定时任务管理

---

## 测试与验证

### `/tests`
**功能作用**：单元测试和集成测试
- pytest 测试框架
- 涵盖核心功能的测试用例

### `/datagen-config-examples`
**功能作用**：数据生成配置示例
- 浏览器任务配置
- 轨迹压缩配置

---

## 文档与资源

### `/docs`
**功能作用**：项目文档
- 安全策略文档
- Kanban 多网关架构文档

### `/assets`
**功能作用**：静态资源
- 项目横幅图片

### `/infographic`
**功能作用**：信息图表
- Kanban 数据库损坏防御图解

---

## 辅助模块

### `/plans`
**功能作用**：功能规划文档
- 新功能的设计文档（如 Gemini OAuth）

### `/.plans`
**功能作用**：计划中的变更
- 尚未实现的功能设计

### `/optional-mcps`
**功能作用**：可选的 MCP 连接器
- Linear 项目管理集成
- n8n 工作流自动化集成

### `/optional-skills`
**功能作用**：可选技能包
- 技能描述和元数据

### `/skills`
**功能作用**：技能定义目录
- AI Agents 相关技能分类
- 领域、游戏、媒体、笔记 productivity 等

---

## 根目录配置文件

| 文件 | 功能作用 |
|------|----------|
| `pyproject.toml` | Python 项目配置 |
| `package.json` | Node.js 项目配置 |
| `Dockerfile` | Docker 镜像构建 |
| `docker-compose.yml` | Docker Compose 配置 |
| `flake.nix` | Nix Flake 配置 |
| `hermes` | 主入口脚本 |
| `cli.py` | CLI 入口 |
| `hermes_state.py` | 状态管理 |
| `hermes_constants.py` | 常量定义 |
| `hermes_logging.py` | 日志系统 |
| `hermes_bootstrap.py` | 启动引导 |

---

## 工作流程

### CI/CD
`.github/workflows/` - GitHub Actions 工作流：
- `tests.yml` - 测试
- `lint.yml` - 代码检查
- `docker-publish.yml` - Docker 发布
- `deploy-site.yml` - 文档部署

### 安全
- `SECURITY.md` - 安全策略
- `supply-chain-audit.yml` - 供应链审计
- `osv-scanner.yml` - 漏洞扫描
