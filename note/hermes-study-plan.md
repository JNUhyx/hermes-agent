# Hermes 学习清单

> 目标：掌握 AI Agent 工程落地能力

---

## 阶段一：从入口开始（1-2天）

### 学习目标
理解 Hermes 的启动流程和 Agent 主循环

### 核心文件
| 序号 | 文件 | 作用 | 学习重点 |
|------|------|------|----------|
| 1 | [cli.py](file:///workspace/cli.py) | CLI 入口 | 参数解析、命令分发 |
| 2 | [hermes_cli/main.py](file:///workspace/hermes_cli/main.py) | CLI 主入口 | 命令路由、子命令实现 |
| 3 | [hermes_bootstrap.py](file:///workspace/hermes_bootstrap.py) | 启动初始化 | 配置加载、环境准备 |
| 4 | [agent/agent_init.py](file:///workspace/agent/agent_init.py) | Agent 实例化 | Agent 核心组件初始化 |
| 5 | [agent/conversation_loop.py](file:///workspace/agent/conversation_loop.py) | 🔑 核心主循环 | "思考→行动→反馈"循环 |

### 关键问题
- Agent 启动时经历了哪些步骤？
- 多轮对话的主循环是什么样的？
- 工具调用流程是如何编排的？

### 实践任务
- [ ] 运行 `hermes --help` 了解命令
- [ ] 在 `conversation_loop.py` 加断点，观察一次完整交互

---

## 阶段二：核心模块（1周）

### 学习目标
掌握 Agent 核心逻辑的实现

### 文件学习顺序

#### 1. 提示词构建
- [ ] [agent/system_prompt.py](file:///workspace/agent/system_prompt.py)
- 理解：提示词如何组合、工具 schema 如何生成

#### 2. 上下文管理
- [ ] [agent/context_engine.py](file:///workspace/agent/context_engine.py)
- 理解：如何管理长对话、什么时候压缩、压缩策略

#### 3. 工具调用
- [ ] [agent/tool_dispatch_helpers.py](file:///workspace/agent/tool_dispatch_helpers.py)
- 理解：工具如何被选择、调用参数如何解析
- [ ] [agent/tool_executor.py](file:///workspace/agent/tool_executor.py)
- 理解：工具执行、结果处理、错误处理

#### 4. 重试与容错
- [ ] [agent/retry_utils.py](file:///workspace/agent/retry_utils.py)
- 理解：指数退避、重试策略、超时控制

#### 5. 记忆与状态
- [ ] [agent/memory_manager.py](file:///workspace/agent/memory_manager.py)
- 理解：Agent 的记忆如何存储和检索

### 关键问题
- 给 LLM 的提示词包含哪些部分？
- 上下文太长了会怎么处理？
- 工具调用失败了会怎么做？

---

## 阶段三：工具系统（1周）

### 学习目标
掌握工具系统的设计和实现

### 核心目录结构
```
tools/
├── registry.py              ← 工具注册中心
├── file_tools.py            ← 文件操作
├── terminal_tool.py        ← Shell 命令执行
├── browser_tool.py          ← 浏览器自动化
├── mcp_tool.py             ← MCP 协议工具
├── web_tools.py            ← Web 搜索
└── computer_use/           ← 计算机使用能力（CUA）
```

### 学习顺序
1. **了解注册机制** → [tools/registry.py](file:///workspace/tools/registry.py)
2. **基础工具**
   - [ ] [tools/file_tools.py](file:///workspace/tools/file_tools.py)
   - [ ] [tools/terminal_tool.py](file:///workspace/tools/terminal_tool.py)
3. **高级工具**
   - [ ] [tools/browser_tool.py](file:///workspace/tools/browser_tool.py)
   - [ ] [tools/computer_use/](file:///workspace/tools/computer_use/)
4. **标准协议**
   - [ ] [tools/mcp_tool.py](file:///workspace/tools/mcp_tool.py)

### 关键问题
- 工具的 schema 怎么定义？
- 工具结果怎么分类（读/写/错误）？
- 安全性如何保证（路径限制、命令白名单）？

### 实践任务
- [ ] 给 `file_tools.py` 加一个新功能（比如文件搜索）
- [ ] 分析一个工具的完整调用链路

---

## 阶段四：平台集成（1周）

### 学习目标
理解消息如何从平台（Slack/Telegram/飞书）到达 Agent 再返回

### 核心目录
```
gateway/
├── run.py                   ← 网关入口
├── session.py               ← 会话管理
├── stream_*.py             ← 流处理
└── platforms/
    ├── telegram.py          ← Telegram
    ├── slack.py             ← Slack
    ├── feishu.py           ← 飞书
    ├── wecom.py            ← 企业微信
    └── whatsapp.py         ← WhatsApp
```

### 学习顺序
1. **先了解网关架构**
   - [ ] [gateway/run.py](file:///workspace/gateway/run.py)
   - [ ] [gateway/session.py](file:///workspace/gateway/session.py)

2. **选一个简单平台深入**（推荐 Telegram 或飞书）
   - [ ] [gateway/platforms/telegram.py](file:///workspace/gateway/platforms/telegram.py)
   - [ ] [gateway/platforms/feishu.py](file:///workspace/gateway/platforms/feishu.py)

### 关键问题
- Webhook 如何接收和处理？
- 消息如何路由到正确的会话？
- 图片/文件/多媒体如何处理？

### 实践任务
- [ ] 读一个平台的 `ADDING_A_PLATFORM.md`（如存在）
- [ ] 画一张消息流程图

---

## 阶段五：插件机制（3-5天）

### 学习目标
掌握插件系统的设计，能自己写插件

### 插件示例参考
```
plugins/
├── spotify/                 ← 简单插件
├── google_meet/             ← 中等复杂度
├── teams_pipeline/          ← 复杂流水线插件
└── security-guidance/       ← 安全插件
```

### 学习顺序
1. **从简单开始**
   - [ ] [plugins/spotify/](file:///workspace/plugins/spotify/)
2. **看复杂插件**
   - [ ] [plugins/teams_pipeline/](file:///workspace/plugins/teams_pipeline/)

### 关键问题
- 插件如何注册和发现？
- 插件如何与 Agent 核心交互？
- 插件的生命周期是什么样的？

### 实践任务
- [ ] 写一个简单插件（比如获取天气）
- [ ] 给插件写单元测试

---

## 阶段六：测试与验证（2-3天）

### 学习目标
从测试用例理解系统设计

### 测试文件
```
tests/
├── test_toolsets.py         ← 工具测试
├── test_trajectory_compressor.py  ← 上下文压缩
├── test_hermes_state.py     ← 状态管理
└── test_gateway_*.py        ← 网关测试
```

### 学习重点
- [ ] 看 `tests/conftest.py` 了解测试基础设施
- [ ] 选你感兴趣的模块，读对应测试

---

## 学习技巧

### 1. 带着问题读
不要从头到尾通读，找问题：
- "工具调用流程是什么？"
- "会话状态存储在哪里？"
- "多平台适配怎么做到的？"

### 2. 边读边画
用流程图/思维导图记录：
- 关键路径（启动流程、工具调用链路）
- 核心数据结构
- 模块依赖关系

### 3. 实际运行观察
```bash
# 调试模式运行，看日志
hermes --debug 2>&1 | tee debug.log

# 看特定模块日志
hermes --debug --log-level=DEBUG 2>&1 | grep "conversation_loop"
```

### 4. 动手改
- 加日志看数据流
- 改参数看变化
- 加小功能验证理解

---

## 学习检查清单

### 入门检查
- [ ] 能说出 Agent 主循环的 3 个步骤
- [ ] 能画出从用户输入到输出的路径
- [ ] 能解释上下文压缩的触发时机

### 进阶检查
- [ ] 能独立写出一个工具
- [ ] 能独立写一个插件
- [ ] 能理解 MCP 协议的作用

### 专家检查
- [ ] 能设计一个新的平台集成
- [ ] 能优化上下文管理策略
- [ ] 能贡献 PR

---

## 进阶学习资源

### 相关标准和协议
- **MCP (Model Context Protocol)**：https://modelcontextprotocol.io
- **Anthropic Computer Use (CUA)**：https://docs.anthropic.com/en/docs/build-with-claude/computer-use

### 其他优秀项目
- OpenAgent / OpenClaw
- AutoGPT / AgentGPT
- LangChain / LlamaIndex

---

*本清单持续更新中，记录学习进度和心得*
