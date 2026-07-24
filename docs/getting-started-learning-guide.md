# Hermes Agent 入门学习指南

> 面向新贡献者 / 新用户的 Hermes Agent 系统化学习文档。
> 阅读本文后，你将理解 Hermes 的整体架构、一条消息从输入到回复的完整旅程、
> 以及如何扩展它（添加工具、命令、技能、插件）。
>
> 配套交互式学习工具：`python learn_hermes.py`（见文末「交互式学习」）。

---

## 目录

1. [Hermes 是什么](#1-hermes-是什么)
2. [心智模型：三层抽象](#2-心智模型三层抽象)
3. [环境准备与首次运行](#3-环境准备与首次运行)
4. [目录结构与关键文件](#4-目录结构与关键文件)
5. [一条消息的完整旅程](#5-一条消息的完整旅程)
6. [核心子系统详解](#6-核心子系统详解)
   - 6.1 [Agent 循环（run_conversation）](#61-agent-循环run_conversation)
   - 6.2 [工具系统（registry / toolsets / tools）](#62-工具系统registry--toolsets--tools)
   - 6.3 [系统提示词（三层缓存友好结构）](#63-系统提示词三层缓存友好结构)
   - 6.4 [会话存储（SessionDB + FTS5）](#64-会话存储sessiondb--fts5)
   - 6.5 [记忆系统（Memory）](#65-记忆系统memory)
   - 6.6 [配置系统（三个 Loader）](#66-配置系统三个-loader)
   - 6.7 [CLI 与斜杠命令注册](#67-cli-与斜杠命令注册)
   - 6.8 [Gateway 与平台适配器](#68-gateway-与平台适配器)
   - 6.9 [插件系统](#69-插件系统)
   - 6.10 [技能（Skills）](#610-技能skills)
   - 6.11 [Cron 定时任务](#611-cron-定时任务)
   - 6.12 [委托（Delegation / 子代理）](#612-委托delegation--子代理)
   - 6.13 [Kanban 多代理看板](#613-kanban-多代理看板)
   - 6.14 [上下文压缩](#614-上下文压缩)
   - 6.15 [Curator 技能管家](#615-curator-技能管家)
7. [如何扩展 Hermes](#7-如何扩展-hermes)
8. [关键约定与陷阱（必读）](#8-关键约定与陷阱必读)
9. [测试](#9-测试)
10. [学习路径与下一步](#10-学习路径与下一步)
11. [交互式学习工具](#11-交互式学习工具)

---

## 1. Hermes 是什么

Hermes Agent 是 [Nous Research](https://nousresearch.com) 开发的**自我改进型 AI 代理**。它的核心特征：

- **闭环学习**：从经验中创建技能（skills）、使用中改进技能、跨会话搜索自己的历史对话、为用户建立深度画像。
- **多入口**：终端 TUI、Telegram、Discord、Slack、WhatsApp、Signal、Email……同一个 Gateway 进程同时服务所有平台。
- **模型无关**：OpenRouter、Anthropic、Nous Portal、NVIDIA、GLM、Kimi、MiniMax、Hugging Face、OpenAI、本地 Ollama……用 `hermes model` 一键切换。
- **可运行在任何地方**：本地、Docker、SSH、Singularity、Modal、Daytona 六种终端后端；可在 $5 VPS 上长跑。
- **可调度**：内置 cron 调度器，自然语言定义任务，定时投递到任意平台。
- **可委派**：派生隔离子代理并行工作，把多步流水线压成「零上下文成本」的一轮。

一句话定位：**一个会学习、会调度、会委派、能从聊天软件驱动云端环境的长跑型 AI 代理框架。**

---

## 2. 心智模型：三层抽象

理解 Hermes，先建立三层心智模型：

```
┌─────────────────────────────────────────────────────────┐
│  用户入口层                                               │
│  CLI (hermes)  |  Gateway (Telegram/Discord/Slack/...)   │
└──────────────────────────┬──────────────────────────────┘
                           │ 消息 / 斜杠命令
┌──────────────────────────▼──────────────────────────────┐
│  代理大脑层 (AIAgent)                                    │
│  系统提示词 + 对话循环 + 工具调度 + 预算/中断 + 压缩      │
└──────────────────────────┬──────────────────────────────┘
                           │ tool_calls / 工具结果
┌──────────────────────────▼──────────────────────────────┐
│  能力层                                                   │
│  Tools(工具)  Skills(技能)  Plugins(插件)  MCP  Memory   │
└─────────────────────────────────────────────────────────┘
```

- **用户入口层**：把人（或消息平台）的输入转换成统一的 `MessageEvent`，把代理的回复投递回去。CLI 和 Gateway 共享大量斜杠命令。
- **代理大脑层**：`AIAgent` 类。维护系统提示词、对话历史、迭代预算；循环调用 LLM、解析 `tool_calls`、执行工具、把结果塞回对话，直到模型给出最终回复。
- **能力层**：代理「会做什么」由这里决定。工具是原子能力（`terminal`、`read_file`、`web_search`……）；技能是过程性记忆（带脚本/模板的 SKILL.md）；插件是宿主外代码（注册工具/钩子/CLI 子命令）；MCP 是接外部服务器的协议；Memory 是持久化用户画像。

> 关键洞察：**工具的「注册」（让 schema 可被查询）和「接线到 toolset」（让模型能调用）是两步独立的操作**。这是新手最容易混淆的点，详见 6.2。

---

## 3. 环境准备与首次运行

### 一键安装（Linux / macOS / WSL2 / Termux）

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes              # 开始对话
```

安装器会装好 uv、Python 3.11、Node.js、ripgrep、ffmpeg。

### 贡献者本地开发路径

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # 安装 uv、创建 venv、安装 .[all]、软链 ~/.local/bin/hermes
./hermes              # 自动探测 venv，无需先 source
```

### 首次配置

```bash
hermes setup          # 完整向导：模型、API key、工具、平台
hermes model          # 选模型/Provider
hermes tools          # 用 curses UI 配置启用的工具集
hermes config set     # 设置单个配置值
hermes doctor         # 诊断问题
```

### 用户配置位置

- `~/.hermes/config.yaml` —— 设置（非密钥）
- `~/.hermes/.env` —— **只放密钥**（API key、token）
- `~/.hermes/logs/` —— 日志（`agent.log` / `errors.log` / `gateway.log`）
- `~/.hermes/state.db` —— 会话 SQLite（FTS5 全文搜索）
- `~/.hermes/skills/` —— 用户技能
- `~/.hermes/plugins/` —— 用户插件

> 注意：代码里**绝不能**硬编码 `~/.hermes`，要用 `get_hermes_home()`（见第 8 节）。

---

## 4. 目录结构与关键文件

```
hermes-agent/
├── run_agent.py          # AIAgent 类（多数方法是到 agent/*.py 的转发）
├── model_tools.py        # 工具编排：discover / get_tool_definitions / handle_function_call
├── toolsets.py           # TOOLSETS 字典 + _HERMES_CORE_TOOLS 默认工具包
├── cli.py                # HermesCLI 交互式 REPL + load_cli_config()
├── hermes_state.py       # SessionDB：SQLite + FTS5 会话存储
├── hermes_constants.py   # get_hermes_home() / display_hermes_home()（profile 感知路径）
├── hermes_logging.py     # setup_logging()
├── agent/                # 代理内部（provider 适配器、循环、压缩、记忆、提示词……）
│   ├── conversation_loop.py     # ★ 真正的主循环 run_conversation()
│   ├── tool_executor.py         # 并发/串行工具执行
│   ├── agent_runtime_helpers.py # invoke_tool() 单工具派发树
│   ├── system_prompt.py         # 三层系统提示词装配
│   ├── prompt_builder.py        # 环境提示、技能提示、上下文文件
│   ├── context_compressor.py    # 上下文压缩器
│   ├── conversation_compression.py # 压缩入口 + 会话切分
│   ├── memory_provider.py       # MemoryProvider ABC
│   ├── memory_manager.py        # 记忆编排器
│   └── agent_init.py            # AIAgent.__init__ 真正逻辑
├── hermes_cli/           # CLI 子命令、设置向导、皮肤引擎、命令注册表
│   ├── main.py            # 入口 + _apply_profile_override()（profile 切换）
│   ├── config.py          # load_config() + DEFAULT_CONFIG + OPTIONAL_ENV_VARS
│   ├── commands.py        # ★ COMMAND_REGISTRY（所有斜杠命令的单一真相源）
│   ├── skin_engine.py     # 数据驱动主题
│   └── curses_ui.py       # 交互式菜单的规范实现（curses）
├── tools/                # 工具实现，通过 registry.register() 自动发现
│   ├── registry.py        # ★ 中央注册表（单例 registry）
│   ├── terminal_tool.py   # 多后端命令执行（本地/docker/modal/ssh/...）
│   ├── todo_tool.py       # 「代理级工具」示例（被 run_agent 拦截）
│   ├── delegate_tool.py   # 子代理委派
│   └── environments/      # 终端后端
├── gateway/              # 消息网关
│   ├── run.py             # GatewayRunner（消息编排、AIAgent 缓存、双消息守卫）
│   ├── session.py         # SessionSource / SessionContext
│   ├── platforms/         # 每个平台一个适配器（telegram.py 等）
│   └── platforms/base.py  # BasePlatformAdapter（_active_sessions / _pending_messages）
├── plugins/              # 插件（model-providers / memory / context_engine / ...）
├── skills/               # 内置技能
├── optional-skills/      # 默认不激活的较重技能
├── cron/                 # jobs.py + scheduler.py（调度器）
├── ui-tui/               # Ink (React) 终端 UI：hermes --tui
├── tui_gateway/         # TUI 的 Python JSON-RPC 后端
├── acp_adapter/         # ACP 服务器（VS Code / Zed / JetBrains 集成）
└── tests/               # pytest 套件（~17k 测试）
```

带 ★ 的是「读源码时优先打开」的文件。

---

## 5. 一条消息的完整旅程

这是理解 Hermes 最重要的一张图。以「用户在 CLI 输入 `帮我看看当前目录有哪些文件`」为例：

```
用户输入
  │
  ▼
HermesCLI 交互循环 (cli.py)
  │  不是斜杠命令 → 构造 user message
  ▼
AIAgent.chat(message)
  └─► run_conversation(message)  → 转发到 agent/conversation_loop.py
        │
        ├─ 1. 预处理：重置重试计数、IterationBudget、设置线程身份
        ├─ 2. 装配/缓存系统提示词（三层：stable / context / volatile）
        ├─ 3. 预取记忆 (_memory_manager.prefetch_all)
        ├─ 4. 插件 pre_llm_call 钩子（上下文注入到 user 消息，不动系统提示词）
        │
        └─► 主循环 while api_call_count < max_iterations and budget.remaining > 0:
              │
              ├─ 中断检查（用户 Ctrl+C / /stop）
              ├─ 消耗预算（带 grace call）
              ├─ 构造 api_messages（注入临时上下文）
              ├─ 修复消息角色交替（_repair_message_sequence）
              ├─ LLM 调用（_interruptible_streaming_api_call）
              ├─ transport.normalize_response(response) 标准化响应
              │
              ├─ if assistant_message.tool_calls:
              │     ├─ 校验工具名（修复幻觉，3 次重试 → 放弃）
              │     ├─ 校验 JSON 参数（3 次重试 → 注入恢复结果）
              │     ├─ 追加 assistant_msg 到 messages
              │     ├─ _execute_tool_calls（并发 or 串行）
              │     │     └─ 对每个 tool_call:
              │     │          ├─ 中断检查
              │     │          ├─ 插件 pre_tool_call 钩子（可拦截）
              │     │          ├─ guardrail 检查
              │     │          ├─ 派发树：
              │     │          │   ├─ 代理级工具（todo/memory/clarify/...）→ 直接调
              │     │          │   └─ 其他 → handle_function_call → registry.dispatch
              │     │          │                                        → entry.handler(args, **kw)
              │     │          │                                        → 返回 JSON 字符串
              │     │          └─ 追加 make_tool_result_message 到 messages
              │     └─ continue（带着工具结果回到 LLM）
              │
              └─ else（无 tool_calls）:
                    final_response = assistant_message.content
                    break
        │
        ├─ 5. 持久化会话到 SQLite
        ├─ 6. 触发记忆/技能 nudge
        └─ 返回 {final_response, messages, api_calls, ...}
  │
  ▼
CLI 渲染回复（Rich 面板 + 皮肤）
```

上例中模型大概率会调用 `terminal` 工具（`ls`），工具返回文件列表，模型据此生成自然语言回复。这就是「一轮 LLM 调用 + 一轮工具调用 + 一轮最终回复」的最小循环。

> 记住三个循环退出条件：**迭代预算耗尽 / 用户中断 / 模型给出无 tool_calls 的最终回复**。

---

## 6. 核心子系统详解

### 6.1 Agent 循环（run_conversation）

**位置**：`agent/conversation_loop.py`（`run_agent.py` 里的 `AIAgent.run_conversation` 只是转发）。

**核心结构**：

```python
while (api_call_count < agent.max_iterations
       and agent.iteration_budget.remaining > 0) or agent._budget_grace_call:
    if agent._interrupt_requested:
        break
    api_call_count += 1
    # ... 构造 api_messages、调用 LLM、标准化 ...
    if assistant_message.tool_calls:
        # 校验 + 执行工具
        agent._execute_tool_calls(assistant_message, messages, ...)
        continue
    final_response = assistant_message.content
    break
```

**关键点**：

- **消息格式全程是 OpenAI 格式**：`{"role": "system|user|assistant|tool", "content": ..., "tool_calls": [...], "tool_call_id": ...}`。reasoning 存在 `assistant_msg["reasoning"]`。
- **角色交替被强制**：`_repair_message_sequence` 在每次 API 调用前修复 `tool→user` 或 `user→user` 尾部（多数 provider 对畸形序列返回空内容）。
- **工具调用有多重恢复路径**：名字幻觉（修复 → 3 次重试 → 放弃）、JSON 参数无效（3 次重试 → 注入恢复结果）、参数截断（拒绝并存为 partial）、reasoning 未闭合（2 次重试）。
- **`_last_content_with_tools`**：模型同时输出内容 + tool_calls 时（常见于 `memory`/`todo` 这类家务工具），内容被留作后备最终回复。
- **`_HOUSEKEEPING_TOOLS`**：`{memory, todo, skill_manage, session_search}`。如果一轮全是家务工具调用，quiet 模式下后续输出会被静音（答案已交付）。
- **预算**：`IterationBudget(max_iterations)`，默认 `max_iterations=90`（与子代理共享）。`_budget_grace_call` 允许耗尽后再跑一轮。`execute_code`-only 的轮次会**退款**。

**新手必读**：`AIAgent` 主要是协调器，真正逻辑在 `agent/` 下的 `conversation_loop.py`、`tool_executor.py`、`agent_runtime_helpers.py`、`system_prompt.py`、`prompt_builder.py`。去那里看，别在 `run_agent.py` 里翻。

---

### 6.2 工具系统（registry / toolsets / tools）

这是 Hermes 最核心、也最容易混淆的子系统。**分清三件事**：

#### (a) 注册：让 schema 可被查询

每个 `tools/*.py` 在模块导入时调用 `registry.register()`：

```python
# tools/todo_tool.py（简化）
from tools.registry import registry

def todo_tool(todos, merge, store) -> str:
    return json.dumps({"todos": todos, "summary": {...}})

registry.register(
    name="todo",
    toolset="todo",
    schema=TODO_SCHEMA,                      # OpenAI function-calling schema
    handler=lambda args, **kw: todo_tool(
        todos=args.get("todos"),
        merge=args.get("merge", False),
        store=kw.get("store")),               # 代理通过 kwargs 注入 per-agent 状态
    check_fn=check_todo_requirements,        # 返回 False 则对模型隐藏
    emoji="📋",
)
```

**自动发现**：`tools/registry.py::discover_builtin_tools()` 用 AST 扫描 `tools/*.py`，只导入模块体里有顶层 `registry.register(...)` 调用的文件。所以**你不需要维护 import 列表**。

**handler 签名**：`(args: dict, **kwargs) -> str`，**必须返回 JSON 字符串**。用 `tool_error()` / `tool_result()` 助手避免样板。

**`check_fn`**：决定工具是否「可用」，结果被 TTL 缓存 30 秒（因为探测 Docker/Modal/Playwright 很慢）。`hermes tools enable` 后调用 `invalidate_check_fn_cache()`。

**`_generation` 计数器**：每次 register/deregister 自增，是 `get_tool_definitions` 缓存失效的信号。

#### (b) 接线到 toolset：让模型能调用

注册只是让 schema 进入注册表；**工具只有出现在某个 toolset 解析后的 `tools` 列表里，才会暴露给模型**。这一步是**手工的、故意的**。

`toolsets.py` 里：

```python
_HERMES_CORE_TOOLS = ["web_search", "terminal", "read_file", "write_file",
                      "patch", "search_files", "vision_analyze", "todo",
                      "memory", "delegate_task", ...]   # 所有平台继承的默认包

TOOLSETS = {
    "hermes-telegram": {"description": "...", "tools": _HERMES_CORE_TOOLS, "includes": []},
    "hermes-discord":  {"description": "...", "tools": _HERMES_CORE_TOOLS + ["discord", "discord_admin"]},
    "debugging":       {"description": "...", "tools": [...], "includes": ["web", "file"]},
    ...
}
```

- **所有平台继承 `_HERMES_CORE_TOOLS`**。改这一处 = 改所有平台的默认能力。
- **`includes` 支持组合 toolset**，`resolve_toolset()` 递归解析（带环检测）。
- **`disabled_toolsets` 永远做减法**，即使对组合 toolset 也生效（issue #17309）。

#### (c) 派发：执行工具

`model_tools.py::handle_function_call()` 是主派发器，但**代理级工具**（`todo`/`memory`/`clarify`/`session_search`/`delegate_task`）在 `agent_runtime_helpers.invoke_tool()` 里被**提前拦截**，因为它们需要 per-agent 状态（`_todo_store`、`_memory_store`、`clarify_callback`），注册表给不了。

派发树大致：

```
invoke_tool()
  ├─ todo            → _todo_tool(store=agent._todo_store)
  ├─ memory          → _memory_tool(store=agent._memory_store) + memory_manager 桥接
  ├─ clarify         → _clarify_tool(callback=agent.clarify_callback)
  ├─ session_search  → _session_search(db=session_db)
  ├─ delegate_task   → agent._dispatch_delegate_task(...)
  └─ 其他            → handle_function_call → registry.dispatch → entry.handler(args, **kw)
                          ↑ 插件 pre/post_tool_call 钩子 + 错误包装成 {"error": ...}
```

**不可信来源的工具结果**（`web_extract`/`web_search`/`browser_*`/`mcp_*`）会被 `make_tool_result_message` 包进语义分隔符，标记为不可信数据 —— 这是**对抗间接提示注入**的架构防线。

> 一句话总结：**注册 = schema 可查；接线 = 模型可见；派发 = 真正执行**。三者独立。

---

### 6.3 系统提示词（三层缓存友好结构）

**位置**：`agent/system_prompt.py`、`agent/prompt_builder.py`。

系统提示词被装配成**三层**，顺序刻意为之（provider 缓存前缀，把稳定内容放前面最大化命中）：

| 层 | 内容 | 变化频率 |
|---|---|---|
| **stable** | 身份（SOUL.md）、任务完成指引、工具感知指引（仅当对应工具在 `valid_tool_names` 时注入 MEMORY_GUIDANCE/SESSION_SEARCH_GUIDANCE 等） | 极少变 |
| **context** | 上下文文件（cwd 的 AGENTS.md/CLAUDE.md/.cursorrules/SOUL.md）+ 调用方 system_message | 每项目不同 |
| **volatile** | 记忆快照、用户画像、外部记忆块、时间戳行（**只有日期，不到分钟**——保持当日 byte 稳定以保住 KV 缓存；PR #20451） | 每会话不同 |

**关键约束**：

- **系统提示词每会话只构建一次并缓存**（`agent._cached_system_prompt`）。除了上下文压缩后 `invalidate_system_prompt()` 重建，**永不重建**。重建会让 Anthropic/OpenAI/OpenRouter 的前缀缓存失效，成本暴涨。
- **插件上下文进 USER 消息，绝不进系统提示词**（见循环里的 `pre_llm_call` 钩子）。
- **改会话中工具集 / 重载记忆 / 重建系统提示词 = 破坏缓存 = 禁止**（压缩除外）。

---

### 6.4 会话存储（SessionDB + FTS5）

**位置**：`hermes_state.py`。

- **存储**：`~/.hermes/state.db`（SQLite，WAL 模式）。表：`sessions`、`messages`、`state_meta`、`compression_locks`，外加两个 FTS5 虚拟表（unicode61 + trigram，后者服务 CJK）。
- **全文搜索**：`search_messages(query)` 用 BM25 跨所有消息搜，带片段抽取、source/role 过滤。CJK 走 trigram 或 LIKE 兜底。
- **写入并发**：`_execute_write()` 用 `BEGIN IMMEDIATE` + 20–150ms 抖动重试（最多 15 次）打散 SQLite convoy。每 50 次写做一次 `wal_checkpoint(PASSIVE)`。
- **WAL 兜底**：NFS/SMB/FUSE 会触发 "locking protocol" 错误，`apply_wal_with_fallback()` 回退到 `DELETE` 模式，**每 (process, db_label) 只告警一次**避免刷爆日志。
- **schema 演进**：`SCHEMA_VERSION = 14`，但**加列不需要 bump**——`_reconcile_columns()` 声明式 diff 现有列并自动补齐。只在重命名/重构时才 bump。
- **删除会话**：把子会话的 `parent_session_id` 置 NULL（而非级联），分支/子代理转写得以幸存。

> 测试时绝不能写 `~/.hermes/`——`tests/conftest.py` 的 `_isolate_hermes_home` autouse fixture 把 `HERMES_HOME` 重定向到临时目录。

---

### 6.5 记忆系统（Memory）

**位置**：`agent/memory_provider.py`（ABC）、`agent/memory_manager.py`（编排器）、`plugins/memory/<name>/`（提供者实现）。

- **`MemoryProvider` ABC**：抽象方法 `name`/`is_available`/`initialize`/`get_tool_schemas`；带默认实现的方法 `prefetch`/`sync_turn`/`shutdown`；可选钩子 `on_turn_start`/`on_session_switch`/`on_pre_compress`/`on_delegation`/`on_memory_write`。
- **`MemoryManager`**：编排**内置提供者 + 至多一个外部提供者**。`add_provider()` 拒绝第二个外部。`handle_tool_call()` 通过 `_tool_to_provider` 索引路由。
- **每轮**：`prefetch_all(user_msg)` → 注入上下文；轮后 `sync_all(...)` → `queue_prefetch_all(...)` 为下一轮预取。
- **`initialize()` 总是收到 `hermes_home`** kwarg —— 提供者必须用它做 profile 隔离存储，禁止 `Path.home()/".hermes"`。
- **`agent_context="cron"` 时跳过写入**——cron 的系统提示词会污染用户画像。
- **政策（2026 年 5 月）**：**不再接受新的 in-tree 记忆提供者**。现有 `plugins/memory/` 集合关闭；新后端必须作为**独立插件仓库**发布到 `~/.hermes/plugins/`。

记忆内容被包进 `<memory-context>` 围栏并标注为「参考数据，非新用户输入」，`StreamingContextScrubber` 在流式时跨 chunk 剥离这些标签。

---

### 6.6 配置系统（三个 Loader）

**位置**：`hermes_cli/config.py`。

**三条加载路径——你必须知道自己在哪条上**：

| Loader | 使用者 | 位置 |
|---|---|---|
| `load_cli_config()` | CLI 模式（`hermes chat`） | `cli.py` |
| `load_config()` | `hermes tools`/`hermes setup`/多数子命令 | `hermes_cli/config.py` |
| 直接 YAML 读 | Gateway 运行时 | `gateway/run.py` + `gateway/config.py` |

**症状诊断**：加了新 key，CLI 看得到但 Gateway 看不到（或反之）→ 你走错了 loader。检查 `DEFAULT_CONFIG` 覆盖面。

**关键点**：

- `DEFAULT_CONFIG` 带 `_config_version`（当前 25）。**只在主动迁移（重命名/重构）时才 bump**；往现有 section 加 key 由深合并自动处理，**不需要 bump**。
- `OPTIONAL_ENV_VARS` 是 `.env` 变量的元数据（描述/prompt/url/password/category）。**`.env` 只放密钥**；非密钥设置（超时、阈值、路径、显示偏好）属于 `config.yaml`。
- 缓存键是 `(path, mtime_ns, size)`，`save_config()` 用 `atomic_yaml_write`（新 inode）让 stat 看到新 mtime → 缓存自动失效。
- `_ENV_VAR_NAME_DENYLIST`：dashboard 环境变量写入器绝不能写的变量（LD_PRELOAD、PYTHONPATH、HERMES_HOME……），防 RCE。
- `_CONFIG_LOCK = threading.RLock()`：libyaml C 扩展并发 `safe_load` 不安全，所有读写串行。

---

### 6.7 CLI 与斜杠命令注册

**位置**：`cli.py`（`HermesCLI`）、`hermes_cli/commands.py`（`COMMAND_REGISTRY`）、`hermes_cli/main.py`（入口）。

**核心设计**：所有斜杠命令定义在**单一真相源** `COMMAND_REGISTRY`（`CommandDef` 列表）。所有下游消费者自动派生：

```
COMMAND_REGISTRY (CommandDef 列表)
   ├─ CLI        process_command() 用 resolve_command() 派发
   ├─ Gateway    GATEWAY_KNOWN_COMMANDS + resolve_command()
   ├─ Gateway 帮助  gateway_help_lines()
   ├─ Telegram   telegram_bot_commands() → BotCommand 菜单
   ├─ Slack      slack_subcommand_map()
   ├─ Discord    discord_skill_commands()
   ├─ 自动补全    SlashCommandCompleter
   └─ CLI 帮助   COMMANDS_BY_CATEGORY
```

**`CommandDef` 字段**：`name`、`description`、`category`（Session/Configuration/Tools & Skills/Info/Exit）、`aliases`、`args_hint`、`subcommands`、`cli_only`、`gateway_only`、`gateway_config_gate`（配置 dotpath，为真时 `cli_only` 命令在 gateway 也可用）。

**加一条斜杠命令**：

1. 在 `COMMAND_REGISTRY` 加 `CommandDef(...)`。
2. 在 `HermesCLI.process_command()` 加 `elif canonical == "mycommand": self._handle_mycommand(...)`。
3. 若 gateway 可用，在 `gateway/run.py` 加 handler。
4. 持久化设置用 `save_config_value()`。

**加别名**只需改 `aliases` 元组——派发、帮助、菜单、自动补全自动更新。

**KawaiiSpinner**（`agent/display.py`）：API 调用时的可爱颜文字动画。皮肤可覆盖脸/动词/翅膀。**绝不用 `\033[K`**（在 `prompt_toolkit.patch_stdout` 下会泄漏成字面 `?[K`），用空格填充 `f"\r{line}{' ' * pad}"`。

**新交互式菜单必须用 `hermes_cli/curses_ui.py`**（`curses_radiolist`/`curses_checklist`）——`simple_term_menu` 在 tmux/iTerm2 有重影 bug，仅作遗留兜底。

---

### 6.8 Gateway 与平台适配器

**位置**：`gateway/run.py`（`GatewayRunner`）、`gateway/platforms/base.py`（`BasePlatformAdapter`）、各平台 `gateway/platforms/<name>.py`。

**消息流（以 Telegram 为例）**：

1. PTB 轮询收到 update → `TelegramAdapter` 建 `MessageEvent` → 调 `BasePlatformAdapter.handle_message()`。
2. **守卫 #1（base adapter）**：检查 `session_key in _active_sessions`：
   - 活跃 → 合并进 `_pending_messages[session_key]`（单槽，最新者胜）或交给 `_busy_session_handler`（busy-input 模式：interrupt/queue/steer）。
   - 空闲 → 获取守卫（`_active_sessions[key] = asyncio.Event()`），spawn `_process_message_background()`。
3. **守卫 #2（gateway runner）**：`_process_message_background()` 里检查 `should_bypass_active_session()`——识别出的命令（`/stop`/`/new`/`/queue`/`/status`/`/approve`/`/deny` 等）**inline 派发**，绕开运行中的 agent。
4. 常规消息：取/建缓存 AIAgent → `run_conversation()` → 流式 token 投递 → 最终回复。
5. 完成：`finally` 释放守卫，检查 `_pending_messages` 有无排队的后续消息。

**两个守卫都必须放行控制命令**——任何要在 agent 阻塞时抵达 runner 的新命令必须**同时绕过两个守卫**并 inline 派发，**不能**走 `_process_message_background()`（会与 session 生命周期竞争）。

**AIAgent 缓存**：`OrderedDict` LRU，max 128，空闲 TTL 1h。**绝不能**每条消息新建 AIAgent——会重建系统提示词，破坏前缀缓存（Anthropic 上约 10x 成本）。

**Scoped lock**：用唯一凭证连接的适配器（bot token、API key）**必须**在 `connect()` 调 `acquire_scoped_lock()`、`disconnect()` 调 `release_scoped_lock()`，防止两个 profile 抢用同一凭证。见 `gateway/platforms/telegram.py` 范式。

**后台进程通知**：`terminal(background=true, notify_on_complete=true)` 时 gateway 跑 watcher 检测完成并触发新 agent 轮。详略由 `display.background_process_notifications` 控制（`all`/`result`/`error`/`off`）。

---

### 6.9 插件系统

**位置**：`hermes_cli/plugins.py`（`PluginManager`/`PluginContext`）、`plugins/<name>/`。

**发现源**（后者覆盖前者）：bundled `<repo>/plugins/` → 用户 `~/.hermes/plugins/` → 项目 `./.hermes/plugins/`（需 `HERMES_ENABLE_PROJECT_PLUGINS`）→ pip entry-points（`hermes_agent.plugins` 组）。

**`PluginContext`** 让插件 `register(ctx)` 能：
- 注册**生命周期钩子**：`pre_tool_call`/`post_tool_call`/`pre_llm_call`/`post_llm_call`/`on_session_start`/`on_session_end`/`transform_terminal_output`/`transform_tool_result`/`transform_llm_output` 等（见 `VALID_HOOKS`）。
- `ctx.register_tool(...)` 注册工具。
- `ctx.register_cli_command(...)` 注册 CLI 子命令（自动接入 `hermes <plugin> <subcmd>`）。
- `ctx.register_skill(...)` / `register_context_engine(...)` / `register_image_gen_provider(...)` / `.llm` 属性（宿主拥有的 `PluginLlm`）。

**两条插件面**：

1. **通用插件**（`hermes_cli/plugins.py` + `plugins/<name>/`）：钩子 + 工具 + CLI 子命令。
2. **模型 provider 插件**（`plugins/model-providers/<name>/`）：单独的**懒发现**系统。每个 `__init__.py` 调 `providers.register_provider(ProviderProfile(...))`。扫描顺序：bundled → user → legacy `providers/<name>.py`。**user 同名覆盖 bundled**，第三方无需改仓库即可替换内置 profile。

**规则**：插件**绝不能改核心文件**（`run_agent.py`/`cli.py`/`gateway/run.py`/`hermes_cli/main.py`）。需要新能力就**扩展通用插件面**（新钩子 / 新 ctx 方法），绝不硬编码插件逻辑进核心。

**发现时机陷阱**：`discover_plugins()` 只是 `import model_tools.py` 的副作用。读插件状态但没先 import `model_tools` 的代码路径**必须显式调** `discover_plugins()`（幂等）。

---

### 6.10 技能（Skills）

**位置**：`skills/`（内置）、`optional-skills/`（默认不激活）、`agent/skill_commands.py`、`tools/skills_hub.py`。

- **技能 = 过程性记忆**：一份 `SKILL.md`（带 frontmatter）+ 可选的 `scripts/`/`references/`/`templates/`。
- **激活**：用户输入 `/<skill-name>`。`skill_commands._build_skill_message()` 做 frontmatter 解析、模板变量替换（`skills.template_vars`）、内联 shell 展开（`skills.inline_shell`）、注入 `[Skill directory: <abs_path>]`（让代理能用 terminal 跑 bundled 脚本）、注入 `[Skill config: ...]`。
- **关键**：技能被作为 **USER 消息**注入（不是系统提示词），以**保住前缀缓存**——这是规范模式。

**SKILL.md frontmatter**：`name`、`description`（≤60 字符，一句，以句号结尾）、`version`、`author`、`license`、`platforms`（OS 门控）、`metadata.hermes.tags`/`.category`/`.related_skills`/`.config`。

**技能编写硬标准**（PR 审核拒绝不合规者）：

1. `description` ≤ 60 字符。
2. 正文中提到的工具必须是**原生 Hermes 工具**（`` `terminal` ``、`` `web_extract` ``、`` `read_file` ``、`` `patch` ``、`` `search_files` ``、`` `delegate_task` ``），**不要**点名已被包装的 shell 工具（`grep`→`search_files`，`cat`→`read_file`，`sed`→`patch`，`find`→`search_files`）。
3. `platforms:` 门控要对照脚本实际 import 审计。POSIX-only 原语（`fcntl`/`termios`/`/proc`/`signal.SIGKILL`/bash heredoc/`osascript`）必须声明平台；**默认先尝试跨平台修**（`tempfile.gettempdir`/`pathlib`/`psutil.pid_exists`）。
4. `author` 先署人类贡献者，"Hermes Agent" 次之。
5. 现代 section 顺序：`# <Skill> Skill` → intro → `## When to Use` → `## Prerequisites` → `## How to Run` → `## Quick Reference` → `## Procedure` → `## Pitfalls` → `## Verification`。复杂技能约 200 行，简单的约 100 行。
6. 脚本进 `scripts/`，参考进 `references/`，模板进 `templates/`。
7. 测试在 `tests/skills/test_<skill>_skill.py`（stdlib + pytest + mock，无网络）。
8. `.env.example` 增量隔离在清晰分隔的块内。

**Skills Hub**（`tools/skills_hub.py`）：从 GitHub / `optional-skills/` 拉技能。`OptionalSkillSource` 获取仓库 `optional-skills/` 下的技能（official，默认不激活，不拷到 `~/.hermes/skills/`）。

---

### 6.11 Cron 定时任务

**位置**：`cron/jobs.py`（job store）、`cron/scheduler.py`（tick 循环）。

**支持的调度格式**：
- 时长：`"30m"`/`"2h"`/`"1d"`（one-shot）
- "every" 短语：`"every 2h"`/`"every monday 9am"`
- 5 字段 cron：`"0 9 * * *"`
- ISO 时间戳（one-shot）：`"2026-06-01T09:00:00Z"`

**关键不变量**：

- `tick()` 用文件锁 `~/.hermes/cron/.tick.lock`（fcntl/msvcrt）防跨进程重复 tick。
- `tick()` **先推进 `next_run_at` 再执行**——at-most-once 语义，崩溃不会重放。
- **catchup 窗口** = 周期一半，钳制 120s–2h；one-shot 有 120s grace。
- **cron 会话默认 `skip_memory=True`**——记忆提供者在 cron 期间不跑（会污染用户画像）。
- **cron 投递不镜像**进目标 gateway 会话——落到自己的 cron 会话，带 header/footer 帧以保住主对话的角色交替。
- profile/workdir 任务**串行**跑（会改 `os.environ`/`TERMINAL_CWD`）；并行安全的任务跑 `ThreadPoolExecutor`。
- 不活跃超时 `HERMES_CRON_TIMEOUT`（默认 600s=10 分钟，`0`=不限），每 5s 轮询活动摘要。

> ⚠️ AGENTS.md 写的「3 分钟硬中断」似乎是文档漂移；实际机制是默认 10 分钟的**不活跃超时**。以代码为准。

**per-job 字段**：`skills`（加载特定技能）、`model`/`provider` 覆盖、`script`（pre-run 数据收集脚本，stdout 注入 prompt；`no_agent=True` 时脚本即整个任务）、`context_from`（链式把 job A 的输出灌进 job B 的 prompt）、`workdir`（在特定目录跑，加载其 AGENTS.md/CLAUDE.md）、多平台投递。

---

### 6.12 委托（Delegation / 子代理）

**位置**：`tools/delegate_tool.py`。

`delegate_task` 派生**隔离子代理**（独立上下文 + 终端会话）。**同步**：父等子摘要再继续；父被中断则子被取消。

**两种形态**：
- **单**：`goal`（+ 可选 `context`/`toolsets`/`role`）。
- **批量（并行）**：`tasks: [...]`，每个一个子代理，并发上限 `delegation.max_concurrent_children`（默认 3）。

**角色**：
- `role="leaf"`（默认）：专注 worker，**不能**调 `delegate_task`/`clarify`/`memory`/`send_message`/`execute_code`。
- `role="orchestrator"`：保留 `delegate_task` 可再派生。门控 `delegation.orchestrator_enabled`（默认 true），深度上限 `delegation.max_spawn_depth`（默认 2）。

**关键点**：

- **`delegate_task` 不持久**。长跑且要跨轮存活的工作用 `cronjob` 或 `terminal(background=True, notify_on_complete=True)`。
- **模型给的 `max_iterations` 被忽略**——config 值（`delegation.max_iterations`）才是权威，模型参数仅保留给内部调用/测试。
- **`_last_resolved_tool_names` 是 `model_tools.py` 的进程全局**——`_run_single_child` 在子代理执行前后保存/恢复它；读它的新代码要知道它在子代理跑期间可能暂时 stale。
- **operator kill switch `is_spawn_paused()`**：检测到失控派生树时冻结新 fan-out，但不中断已在跑的子。
- **心跳线程**周期性 `parent_agent._touch_activity(desc)`，防 gateway 不活跃超时误触。

---

### 6.13 Kanban 多代理看板

**位置**：`hermes_cli/kanban.py`（CLI）、`hermes_cli/kanban_db.py`（DB 层）、`tools/kanban_tools.py`（代理工具）、`plugins/kanban/`（dashboard + systemd）。

**持久 SQLite 看板**，让多 profile / worker 协作共享任务。

- **CLI 动词**：`init`/`boards`/`create`/`swarm`/`list`/`show`/`assign`/`claim`/`complete`/`block`/`archive`/`dispatch`/`daemon`/`watch`/`stats`/`tail`/`log` 等。
- **worker/orchestrator toolset**（`tools/kanban_tools.py`）：worker 8 工具（`kanban_show`/`kanban_complete`/`kanban_block`/`kanban_heartbeat`/`kanban_comment`/`kanban_create`/`kanban_link`），orchestrator 额外 2 个（`kanban_list`/`kanban_unblock`）。**不在 kanban 任务时 schema 占用为零**（`check_fn=_check_kanban_mode`）。
- **dispatcher**：长跑循环（默认每 60s）回收 stale claim、推进 ready、原子 claim、派生被指派的 profile。默认**跑在 gateway 内**（`kanban.dispatch_in_gateway: true`）。

**隔离模型**：

- **Board 是硬边界**——worker 用 `HERMES_KANBAN_BOARD` 锁定 env，看不到别的 board。
- **Tenant 是 board 内软命名空间**——一个专家车队可服务多个业务（workspace-path + memory-key 隔离）。
- 连续 `kanban.failure_limit` 次（默认 2）非成功自动 block，防空转。
- **worker 任务归属强制**（`_enforce_worker_task_owner`）：带 `HERMES_KANBAN_TASK` 的进程拒绝显式 `task_id` 指向他人任务的参数（防 prompt 注入的 worker 破坏兄弟/跨租户运行，#19534）。

**为什么用工具而非 `hermes kanban` shell-out**：worker 的 terminal 可能指向 Docker/Modal/SSH，没法在容器内跑 `hermes`；工具在 agent Python 进程内跑，总能触达 `~/.hermes/kanban.db`；且结构化参数避免 shlex 脆弱性。

---

### 6.14 上下文压缩

**位置**：`agent/context_compressor.py`、`agent/conversation_compression.py`。

> 这是**唯一允许**中途改过去上下文的场景（AGENTS.md 明示）。其他地方破坏 prompt 缓存 = 禁止。

**流程**（`compress_context`）：

1. **懒可行性检查**：首次尝试时 `check_compression_model_feasibility(agent)`，aux 模型上下文窗 < 主阈值则告警并自动降低会话阈值。
2. **压缩锁**（`state.db` 的 `compression_locks` 表，持锁者 id = `pid:tid:agent:uuid`）：防两个共享 session_id 的 AIAgent 同时轮转。锁子系统缺失时**fail-open**（宁可冒险也不无限空转）。
3. **通知记忆提供者** `on_pre_compress(messages)`——在丢弃前抽取洞察。
4. **压缩**：用 aux（便宜快）模型摘要中段，保护头尾。token 预算尾部保护（非固定消息数）。LLM 摘要前先做工具输出裁剪（廉价预筛）。失败则返回 messages 不变，会话不轮转。
5. **会话切分 + 轮转**（仅成功时）：`end_session(old, "compression")` → 新 `session_id`（`parent_session_id = old`）→ `create_session` → 重建系统提示词 → 通知上下文引擎 `on_session_start(boundary_reason="compression")` → 通知记忆提供者 `on_session_switch(reset=False, reason="compression")` → 清文件去重缓存。
6. 连续压缩 ≥2 次会告警（质量递减）。

**`SUMMARY_PREFIX`** 是承重提示工程：标注摘要为「参考背景，非活动指令」，让模型只回最新 user 消息，在最新消息偏离时丢弃过期的 `## Active Task`，并明示系统提示词里的持久记忆（MEMORY.md/USER.md）**永远**权威。改它要把旧版加进 `_HISTORICAL_SUMMARY_PREFIXES` 以便再规范化时剥离残留指令。

`/compress` 斜杠命令用 `force=True` 绕过摘要失败冷却，可立即重试。

---

### 6.15 Curator 技能管家

**位置**：`agent/curator.py`、`agent/curator_backup.py`、`tools/skill_usage.py`、`hermes_cli/curator.py`。

后台技能维护系统：跟踪 agent 创建的技能用量，自动归档过时的。**用户永不丢技能**——归档进 `~/.hermes/skills/.archive/` 可恢复。

- **遥测**：`tools/skill_usage.py` 维护 sidecar `~/.hermes/skills/.usage.json`——每技能 `use_count`/`view_count`/`patch_count`/`last_activity_at`/`state`（active/stale/archived）/`pinned`。fcntl/msvcrt 跨进程锁。
- **不变量**：
  - 只动 `created_by: "agent"` 的技能——bundled + hub 安装的不可碰。
  - **永不删除**，最多归档，且可恢复。
  - **pinned 技能豁免所有自动转换和 LLM 审查**；`skill_manage(action="delete")` 拒绝 pinned；patch/edit/write_file/remove_file 放行以便持续改进。
  - 用 auxiliary 客户端，**绝不碰主会话提示词缓存**。状态存 `~/.hermes/skills/.curator_state`。
- **CLI 动词**：`status`/`run`/`pause`/`resume`/`pin`/`unpin`/`archive`/`restore`/`prune`/`backup`/`rollback`。

---

## 7. 如何扩展 Hermes

### 7.1 添加工具

**首选：插件路由**（本地/自定义工具别改核心）：

```bash
# ~/.hermes/plugins/mytool/plugin.yaml
name: mytool
version: 1.0.0
description: "Does X."
author: you
kind: standalone
provides_tools: [my_tool]
```

```python
# ~/.hermes/plugins/mytool/__init__.py
def register(ctx):
    ctx.register_tool(
        name="my_tool",
        toolset="mytool",
        schema={"name": "my_tool", "description": "...", "parameters": {...}},
        handler=lambda args, **kw: json.dumps({"success": True}),
        requires_env=["MY_API_KEY"],
    )
```

插件工具集自动发现，可免改 `tools/` 和 `toolsets.py` 启停。

**内置路由**（贡献核心 Hermes 工具时）：

1. 创建 `tools/your_tool.py`，模块级 `registry.register(...)`。
2. 在 `toolsets.py` 加入 `_HERMES_CORE_TOOLS`（全平台）或新 toolset。**这步必须**——自动发现只让 schema 可查，工具只有进 toolset 解析列表才暴露给模型。

**handler 规则**：
- 签名 `(args: dict, **kwargs) -> str`，**必须返回 JSON 字符串**。
- 用 `tool_error()` / `tool_result()` 助手。
- 持久状态用 `get_hermes_home()` 基目录，**绝不** `Path.home()/".hermes"`。
- schema 描述里若提文件路径，用 `display_hermes_home()` 让其 profile 感知。
- **禁止**在 schema 描述里硬编码跨 toolset 工具名引用（工具可能不可用导致幻觉）；需要的话在 `get_tool_definitions()` 动态加（见 `browser_navigate`/`execute_code` 后处理块）。

### 7.2 添加斜杠命令

1. 在 `hermes_cli/commands.py` 的 `COMMAND_REGISTRY` 加 `CommandDef(...)`。
2. 在 `cli.py` 的 `process_command()` 加 `elif canonical == "mycommand": self._handle_mycommand(cmd_original)`。
3. gateway 可用则加 `gateway/run.py` handler。
4. 持久设置用 `save_config_value()`。

加别名只改 `aliases` 元组。

### 7.3 添加技能

`~/.hermes/skills/<category>/<name>/SKILL.md` + 可选 `scripts/`/`references/`/`templates/`。遵守第 6.10 节的硬标准。复杂约 200 行，简单约 100 行。

### 7.4 添加配置

`config.yaml` 新 key → 加到 `hermes_cli/config.py` 的 `DEFAULT_CONFIG`。往现有 section 加 key **不需要** bump `_config_version`（深合并处理）；重命名/重构才 bump。

`.env` 变量（仅密钥）→ 加到 `OPTIONAL_ENV_VARS` 带元数据。

### 7.5 添加模型 Provider 插件

`plugins/model-providers/<name>/__init__.py` 调 `providers.register_provider(ProviderProfile(...))`。完整指南见 `website/docs/developer-guide/model-provider-plugin.md`。

---

## 8. 关键约定与陷阱（必读）

| # | 规则 | 为什么 |
|---|---|---|
| 1 | **用 `get_hermes_home()`**（代码路径）/ `display_hermes_home()`（用户消息），**绝不**硬编码 `~/.hermes` | 破坏 profile 隔离（PR #3575 修了 5 个 bug） |
| 2 | **测试要同时 mock `Path.home()` 和设 `HERMES_HOME`** | 代码读 env var，不只读 `Path.home()` |
| 3 | **prompt 缓存不能破**：不改过去上下文、不改会话中工具集、不重载记忆/重建系统提示词 | 重建让 Anthropic/OpenAI 前缀缓存失效，成本暴涨 |
| 4 | **改系统提示词状态的斜杠命令要 cache-aware**：默认延迟失效（下会话生效），`--now` opt-in 立即 | 同上 |
| 5 | **spinner/display 绝不用 `\033[K`** | 在 `prompt_toolkit.patch_stdout` 下泄漏成字面 `?[K`，用 `f"\r{line}{' ' * pad}"` |
| 6 | **新交互菜单用 `hermes_cli/curses_ui.py`**，不用 `simple_term_menu` | 后者在 tmux/iTerm2 重影 |
| 7 | **gateway 有两个消息守卫**，控制命令要同时绕过并 inline 派发 | 走 `_process_message_background` 会与 session 生命周期竞争 |
| 8 | **`_last_resolved_tool_names` 是进程全局**，子代理执行期间可能 stale | delegate_tool 保存/恢复它 |
| 9 | **schema 描述禁止硬编码跨 toolset 工具名引用** | 工具可能不可用导致模型幻觉调用 |
| 10 | **工具 handler 必须返回 JSON 字符串** | registry 不包装返回值，原样返回 |
| 11 | **`delegate_task` 不持久** | 同步、父等子；长跑用 cronjob 或 `terminal(background=True)` |
| 12 | **不再接受新 in-tree 记忆提供者** | 政策（2026-05），新后端发独立插件仓库 |
| 13 | **插件绝不能改核心文件** | 扩展通用插件面（新钩子/新 ctx 方法） |
| 14 | **测试不写 `~/.hermes/`** | `_isolate_hermes_home` autouse fixture 重定向到临时目录 |
| 15 | **用 `scripts/run_tests.sh`，别直接 `pytest`** | 保 CI 对等（清密钥、TZ=UTC、LANG=C.UTF-8、subprocess 隔离） |
| 16 | **依赖必须有上界** | PyPI `>=floor,<next_major`；pre-1.0 `<0.(minor+2)`；git URL 锁 SHA |
| 17 | **三个 config loader**：CLI / 子命令 / gateway 直读 YAML | key 在一边可见另一边不可见 = 走错 loader |
| 18 | **别写 change-detector 测试** | 测行为契约（关系/不变量），不快照数据（catalog 名、config 版本号、枚举数） |

---

## 9. 测试

```bash
scripts/run_tests.sh                          # 全套，CI 对等
scripts/run_tests.sh tests/gateway/           # 一个目录
scripts/run_tests.sh tests/agent/test_foo.py::test_x   # 一个测试
scripts/run_tests.sh -v --tb=long            # 透传 pytest 参数
scripts/run_tests.sh --no-isolate tests/foo/  # 关掉子进程隔离（调试更快）
```

**subprocess-per-test 隔离**：每个测试跑在全新 spawn 出的 Python 子进程里（`tests/_isolate_plugin.py`），模块级 dict/set/ContextVar 不会跨测试泄漏。每测试开销 ~0.5–1.0s，xdist 并行摊销。

**为什么必须用 wrapper**：清掉 `*_API_KEY`/`*_TOKEN`（防本地密钥泄漏）、`HOME`/`~/.hermes/` 重定向到临时目录、TZ=UTC、LANG=C.UTF-8、`-n auto` 安全（隔离防跨 worker flake）。

**写测试的黄金法则**：

- ✅ 测行为契约：「catalog 里每个模型都有 context-length 条目」「迁移后用户版本 == 当前最新」。
- ❌ 别测数据快照：「`_PROVIDER_MODELS["huggingface"]` 长度为 8」「`_config_version == 25`」——这些是 change-detector，每次数据更新就坏。

---

## 10. 学习路径与下一步

**入门（1–2 天）**：

1. 跑 `./setup-hermes.sh` + `hermes setup`，完成首对话。
2. 读 `README.md` 和本指南。
3. 跑 `python learn_hermes.py` 过一遍交互式课程。
4. 用 `hermes`、`/help`、`/skills`、`/model`、`/tools` 摸熟 CLI。

**进阶（3–5 天）**：

5. 读 [tools/registry.py](file:///workspace/tools/registry.py) 全文（小而关键）。
6. 读 [toolsets.py](file:///workspace/toolsets.py) 的 `_HERMES_CORE_TOOLS` 和 `TOOLSETS`。
7. 跟着第 5 节的图，读 [agent/conversation_loop.py](file:///workspace/agent/conversation_loop.py) 的主循环。
8. 读 [tools/todo_tool.py](file:///workspace/tools/todo_tool.py) + [tools/terminal_tool.py](file:///workspace/tools/terminal_tool.py) 看真实工具实现。
9. 用插件路由写一个自定义工具（第 7.1 节）。

**深入（持续）**：

10. 读 [agent/system_prompt.py](file:///workspace/agent/system_prompt.py) + [agent/prompt_builder.py](file:///workspace/agent/prompt_builder.py) 理解三层提示词。
11. 读 [gateway/run.py](file:///workspace/gateway/run.py) + [gateway/platforms/base.py](file:///workspace/gateway/platforms/base.py) 理解双守卫。
12. 读 [hermes_cli/commands.py](file:///workspace/hermes_cli/commands.py) 理解命令注册派生。
13. 读 [agent/context_compressor.py](file:///workspace/agent/context_compressor.py) 理解唯一允许的上下文突变。
14. 跑 `scripts/run_tests.sh tests/agent/` 看测试如何断言行为。

**贡献**：读 `CONTRIBUTING.md` 和官方 [Contributing 指南](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)。

---

## 11. 交互式学习工具

仓库根目录的 `learn_hermes.py` 是配套的**交互式 CLI 学习程序**，把本指南浓缩成分章课程 + 随堂测验。

```bash
python learn_hermes.py            # 交互式菜单（需 TTY）
python learn_hermes.py --list     # 列出所有课程
python learn_hermes.py --show 1   # 非交互打印第 1 课
python learn_hermes.py --all      # 非交互打印全部课程
```

特性：

- 分章课程，带代码示例和「深入阅读」文件指针。
- 每课随堂测验（多选），即时反馈 + 计分。
- 进度持久化到 `~/.hermes_learn_progress.json`。
- 命令：数字选课、`n`/`p` 翻页、`m` 回菜单、`r` 重测、`q` 退出、`h` 帮助。
- 仅用 Python 标准库，无需 venv 即可运行。

跑起来玩一玩，边答边学。
