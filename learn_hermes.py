#!/usr/bin/env python3
"""Hermes Agent 交互式学习工具（Interactive Learning CLI）.

把 docs/getting-started-learning-guide.md 浓缩成分章课程 + 随堂测验。
仅依赖 Python 标准库，无需 venv 即可运行。

用法:
    python learn_hermes.py             # 交互式菜单（需 TTY）
    python learn_hermes.py --list      # 列出所有课程
    python learn_hermes.py --show 1    # 非交互打印第 1 课
    python learn_hermes.py --all        # 非交互打印全部课程
    python learn_hermes.py --reset     # 清空进度

交互命令（菜单内）:
    数字    选择对应课程
    h       帮助
    q       退出

交互命令（课程内）:
    Enter/n 下一页
    p        上一页
    m        返回菜单
    r        重做本课测验
    q        退出
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# --------------------------------------------------------------------------- #
# 进度持久化
# --------------------------------------------------------------------------- #

PROGRESS_PATH = Path.home() / ".hermes_learn_progress.json"

# ANSI 颜色（检测非 TTY / NO_COLOR 时禁用）
_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(t: str) -> str:
    return _c("1", t)


def dim(t: str) -> str:
    return _c("2", t)


def cyan(t: str) -> str:
    return _c("36", t)


def green(t: str) -> str:
    return _c("32", t)


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


def magenta(t: str) -> str:
    return _c("35", t)


# --------------------------------------------------------------------------- #
# 数据模型
# --------------------------------------------------------------------------- #


@dataclass
class Question:
    prompt: str
    options: List[str]
    answer: int  # 正确选项的索引（从 0 起）
    explain: str = ""


@dataclass
class Lesson:
    id: int
    title: str
    summary: str  # 菜单里的一行摘要
    pages: List[str]  # 每页是一段 markdown 文本（可含 ``` 代码块）
    questions: List[Question] = field(default_factory=list)
    further_reading: List[str] = field(default_factory=list)  # 文件指针


# --------------------------------------------------------------------------- #
# 课程内容
# --------------------------------------------------------------------------- #

LESSONS: List[Lesson] = []


def _L(
    lid: int,
    title: str,
    summary: str,
    pages: List[str],
    questions: Optional[List[Question]] = None,
    further_reading: Optional[List[str]] = None,
) -> None:
    LESSONS.append(
        Lesson(
            id=lid,
            title=title,
            summary=summary,
            pages=pages,
            questions=questions or [],
            further_reading=further_reading or [],
        )
    )


# ---- 课 1：Hermes 是什么与心智模型 ---------------------------------------- #
_L(
    1,
    "Hermes 是什么 & 心智模型",
    "定位、特征、三层抽象",
    [
        """# 第 1 课：Hermes 是什么 & 心智模型

Hermes Agent 是 Nous Research 开发的**自我改进型 AI 代理**。核心特征：

- **闭环学习**：从经验中创建技能、使用中改进、跨会话搜索历史、为用户建模。
- **多入口**：终端 TUI、Telegram、Discord、Slack、WhatsApp、Signal、Email——同一 Gateway 进程。
- **模型无关**：OpenRouter / Anthropic / Nous Portal / GLM / Kimi / MiniMax / 本地 Ollama……`hermes model` 一键切。
- **可运行在任何地方**：本地、Docker、SSH、Singularity、Modal、Daytona 六种终端后端。
- **可调度 / 可委派**：内置 cron；派生子代理并行工作。

一句话：**会学习、会调度、会委派、能从聊天软件驱动云端环境的长跑型代理框架。**""",
        """## 三层心智模型

理解 Hermes，先建立三层抽象：

```
┌─────────────────────────────────────────────────────┐
│  用户入口层                                          │
│  CLI (hermes) | Gateway (Telegram/Discord/Slack/...) │
└──────────────────────────┬──────────────────────────┘
                           │ 消息 / 斜杠命令
┌──────────────────────────▼──────────────────────────┐
│  代理大脑层 (AIAgent)                                │
│  系统提示词 + 对话循环 + 工具调度 + 预算/中断 + 压缩  │
└──────────────────────────┬──────────────────────────┘
                           │ tool_calls / 工具结果
┌──────────────────────────▼──────────────────────────┐
│  能力层                                              │
│  Tools(工具) Skills(技能) Plugins(插件) MCP Memory   │
└─────────────────────────────────────────────────────┘
```

- **入口层**：把人或平台的输入转成统一 `MessageEvent`，把回复投递回去。CLI 和 Gateway 共享大量斜杠命令。
- **大脑层**：`AIAgent` 维护系统提示词、对话历史、迭代预算；循环调 LLM、解析 `tool_calls`、执行工具、把结果塞回，直到模型给出最终回复。
- **能力层**：代理「会做什么」。工具是原子能力；技能是过程性记忆（SKILL.md）；插件是宿主外代码；MCP 接外部服务器；Memory 是持久画像。

> 关键洞察：**工具的「注册」和「接线到 toolset」是两步独立操作**。第 6 课详述。""",
    ],
    [
        Question(
            prompt="Hermes 的「闭环学习」最不准确的说法是？",
            options=[
                "从经验中创建技能",
                "使用中改进技能",
                "跨会话搜索自己的历史对话",
                "每次对话都重建系统提示词",
            ],
            answer=3,
            explain="系统提示词每会话只构建一次并缓存，重建会破坏 prompt 缓存（成本暴涨）。闭环学习靠技能/记忆/session_search，而非重建提示词。",
        ),
        Question(
            prompt="下列哪个不属于「能力层」？",
            options=["Tools（工具）", "Skills（技能）", "Gateway Runner", "MCP"],
            answer=2,
            explain="Gateway Runner 属于「用户入口层」，负责消息编排、AIAgent 缓存、双消息守卫。",
        ),
    ],
    further_reading=[
        "README.md",
        "docs/getting-started-learning-guide.md",
    ],
)

# ---- 课 2：环境准备与目录结构 --------------------------------------------- #
_L(
    2,
    "环境准备与目录结构",
    "安装、配置位置、关键文件地图",
    [
        """# 第 2 课：环境准备与目录结构

## 安装

一键安装（Linux / macOS / WSL2）：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes
```

贡献者本地开发：

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # 装 uv、建 venv、装 .[all]、软链 hermes
./hermes              # 自动探测 venv
```

## 用户配置位置

- `~/.hermes/config.yaml` —— 设置（非密钥）
- `~/.hermes/.env` —— **只放密钥**（API key、token）
- `~/.hermes/logs/` —— `agent.log` / `errors.log` / `gateway.log`
- `~/.hermes/state.db` —— 会话 SQLite（FTS5）
- `~/.hermes/skills/` —— 用户技能
- `~/.hermes/plugins/` —— 用户插件

> 代码里**绝不能**硬编码 `~/.hermes`，要用 `get_hermes_home()`（第 9 课）。""",
        """## 关键文件地图（读源码优先打开 ★）

```
hermes-agent/
├── run_agent.py          # AIAgent 类（多为转发到 agent/*.py）
├── model_tools.py        # 工具编排：discover / get_tool_definitions / handle_function_call
├── toolsets.py           # TOOLSETS 字典 + _HERMES_CORE_TOOLS 默认包
├── cli.py                # HermesCLI 交互式 REPL + load_cli_config()
├── hermes_state.py       # SessionDB：SQLite + FTS5
├── hermes_constants.py   # get_hermes_home() / display_hermes_home()
├── agent/                # 代理内部
│   ├── conversation_loop.py     # ★ 真正的主循环
│   ├── tool_executor.py         # 并发/串行工具执行
│   ├── system_prompt.py         # 三层系统提示词
│   ├── context_compressor.py    # 上下文压缩器
│   └── memory_manager.py        # 记忆编排器
├── hermes_cli/
│   ├── commands.py        # ★ COMMAND_REGISTRY（所有斜杠命令单一真相源）
│   ├── config.py          # load_config() + DEFAULT_CONFIG
│   └── curses_ui.py       # 交互式菜单规范实现
├── tools/
│   ├── registry.py        # ★ 中央注册表（单例 registry）
│   └── delegate_tool.py   # 子代理委派
├── gateway/
│   ├── run.py             # GatewayRunner（双消息守卫）
│   └── platforms/base.py  # BasePlatformAdapter
└── plugins/               # 插件（model-providers / memory / ...）
```

记住带 ★ 的文件——它们是理解 Hermes 的脊柱。""",
    ],
    [
        Question(
            prompt="API key 应该放在哪里？",
            options=["config.yaml", ".env", "agent.log", "state.db"],
            answer=1,
            explain="`.env` 只放密钥；非密钥设置（超时、阈值、路径、显示偏好）属于 config.yaml。",
        ),
        Question(
            prompt="真正的 agent 主循环在哪个文件？",
            options=["run_agent.py", "model_tools.py", "agent/conversation_loop.py", "cli.py"],
            answer=2,
            explain="run_agent.py 里的 AIAgent.run_conversation 只是转发到 agent/conversation_loop.py。真正的循环逻辑在那里。",
        ),
    ],
    further_reading=[
        "hermes_constants.py",
        "tools/registry.py",
        "agent/conversation_loop.py",
    ],
)

# ---- 课 3：一条消息的完整旅程 --------------------------------------------- #
_L(
    3,
    "一条消息的完整旅程",
    "从输入到回复的全流程",
    [
        """# 第 3 课：一条消息的完整旅程

以「用户在 CLI 输入 `帮我看看当前目录有哪些文件`」为例：

```
用户输入
  │
  ▼
HermesCLI 交互循环 (cli.py)
  │  不是斜杠命令 → 构造 user message
  ▼
AIAgent.chat(message)
  └─► run_conversation(message) → 转发到 agent/conversation_loop.py
        │
        ├─ 1. 预处理：重置重试计数、IterationBudget、设置线程身份
        ├─ 2. 装配/缓存系统提示词（三层：stable/context/volatile）
        ├─ 3. 预取记忆 (prefetch_all)
        ├─ 4. 插件 pre_llm_call 钩子（上下文注入到 user 消息）
        │
        └─► 主循环 while api_call_count < max_iter and budget.remaining > 0:
              ├─ 中断检查
              ├─ 消耗预算（带 grace call）
              ├─ 构造 api_messages、修复角色交替
              ├─ LLM 调用 → normalize_response
              ├─ if tool_calls:
              │     ├─ 校验工具名（修复幻觉，3 次重试 → 放弃）
              │     ├─ 校验 JSON 参数（3 次重试 → 注入恢复）
              │     └─ _execute_tool_calls（并发/串行）→ 结果塞回 messages → continue
              └─ else: final_response = content; break
        │
        ├─ 5. 持久化会话到 SQLite
        └─ 6. 触发记忆/技能 nudge → 返回 {final_response, messages, ...}
```

上例模型大概率调 `terminal` 工具（`ls`），工具返回文件列表，模型据此生成回复。这就是「一轮 LLM + 一轮工具 + 一轮最终回复」的最小循环。""",
        """## 三个循环退出条件

1. **迭代预算耗尽**（默认 max_iterations=90，与子代理共享）。
2. **用户中断**（Ctrl+C / `/stop`）。
3. **模型给出无 tool_calls 的最终回复**。

## 关键细节

- **消息全程 OpenAI 格式**：`{"role": "system|user|assistant|tool", ...}`，reasoning 存在 `assistant_msg["reasoning"]`。
- **角色交替被强制**：`_repair_message_sequence` 在每次 API 调用前修复 `tool→user` 或 `user→user` 尾部。
- **不可信工具结果**（`web_extract`/`web_search`/`browser_*`/`mcp_*`）被 `make_tool_result_message` 包进语义分隔符——**对抗间接提示注入**的架构防线。
- **`execute_code`-only 的轮次会退款预算**。
- **`_budget_grace_call`**：预算耗尽后允许再跑一轮。""""",
    ],
    [
        Question(
            prompt="哪个不是 agent 主循环的退出条件？",
            options=[
                "迭代预算耗尽",
                "用户中断",
                "模型给出无 tool_calls 的最终回复",
                "工具执行失败",
            ],
            answer=3,
            explain="工具失败只是把错误结果塞回 messages 继续循环（多重重试路径），不会退出主循环。",
        ),
        Question(
            prompt="为什么不可信工具结果（web_extract 等）要被包进语义分隔符？",
            options=[
                "为了节省 token",
                "对抗间接提示注入",
                "加速渲染",
                "避免重复缓存",
            ],
            answer=1,
            explain="标记为不可信数据，防止网页内容里藏的指令劫持模型行为。这是架构级防线。",
        ),
    ],
    further_reading=[
        "agent/conversation_loop.py",
        "agent/tool_dispatch_helpers.py",
    ],
)

# ---- 课 4：工具系统 ----------------------------------------------------- #
_L(
    4,
    "工具系统（registry / toolsets / tools）",
    "注册、接线、派发三步独立",
    [
        """# 第 4 课：工具系统

最核心、最易混淆的子系统。**分清三件事**：

## (a) 注册：让 schema 可被查询

每个 `tools/*.py` 在模块导入时调 `registry.register()`：

```python
# tools/todo_tool.py（简化）
from tools.registry import registry

def todo_tool(todos, merge, store) -> str:
    return json.dumps({"todos": todos, "summary": {...}})

registry.register(
    name="todo",
    toolset="todo",
    schema=TODO_SCHEMA,            # OpenAI function-calling schema
    handler=lambda args, **kw: todo_tool(
        todos=args.get("todos"),
        merge=args.get("merge", False),
        store=kw.get("store")),     # 代理通过 kwargs 注入 per-agent 状态
    check_fn=check_todo_requirements,  # 返回 False 则对模型隐藏
    emoji="📋",
)
```

- **自动发现**：`discover_builtin_tools()` 用 AST 扫描 `tools/*.py`，只导入模块体里有顶层 `registry.register(...)` 的文件。无需维护 import 列表。
- **handler 签名**：`(args: dict, **kwargs) -> str`，**必须返回 JSON 字符串**。用 `tool_error()` / `tool_result()` 助手。
- **`check_fn`**：决定可用性，结果 TTL 缓存 30 秒（探测 Docker/Modal/Playwright 很慢）。`hermes tools enable` 后调 `invalidate_check_fn_cache()`。
- **`_generation` 计数器**：每次 register/deregister 自增，是缓存失效信号。""",
        """## (b) 接线到 toolset：让模型能调用

注册只让 schema 进注册表；**工具只有出现在某 toolset 解析后的 `tools` 列表里，才暴露给模型**。这步是**手工的、故意的**。

```python
# toolsets.py
_HERMES_CORE_TOOLS = ["web_search", "terminal", "read_file",
                      "write_file", "patch", "search_files", ...]

TOOLSETS = {
    "hermes-telegram": {"tools": _HERMES_CORE_TOOLS, "includes": []},
    "hermes-discord":  {"tools": _HERMES_CORE_TOOLS + ["discord", "discord_admin"]},
    "debugging":       {"tools": [...], "includes": ["web", "file"]},
}
```

- **所有平台继承 `_HERMES_CORE_TOOLS`**——改这一处 = 改所有平台默认能力。
- **`includes` 支持组合**，`resolve_toolset()` 递归解析（带环检测）。
- **`disabled_toolsets` 永远做减法**，即使对组合 toolset 也生效。

## (c) 派发：执行工具

`handle_function_call()` 是主派发器，但**代理级工具**（`todo`/`memory`/`clarify`/`session_search`/`delegate_task`）在 `invoke_tool()` 里被**提前拦截**——它们需要 per-agent 状态（`_todo_store`/`_memory_store`/`clarify_callback`），注册表给不了。

```
invoke_tool()
  ├─ todo/memory/clarify/session_search/delegate_task → 直接调（带 per-agent store）
  └─ 其他 → handle_function_call → registry.dispatch → entry.handler(args, **kw)
                                          ↑ pre/post_tool_call 钩子 + 错误包成 {"error":...}
```

> **一句话**：注册 = schema 可查；接线 = 模型可见；派发 = 真正执行。三者独立。""",
    ],
    [
        Question(
            prompt="注册一个工具后，模型就一定能调用它了吗？",
            options=[
                "是，注册即可用",
                "否，还必须出现在某 toolset 解析后的 tools 列表里",
                "否，还要写 import 语句",
                "是，只要 check_fn 返回 True",
            ],
            answer=1,
            explain="注册只让 schema 可查；接线到 toolset 才让模型可见。这是新手最易混淆的点。",
        ),
        Question(
            prompt="工具 handler 的返回值必须是？",
            options=["dict", "JSON 字符串", "list", "任意对象"],
            answer=1,
            explain="必须返回 JSON 字符串。registry 不包装返回值，原样返回。用 tool_error()/tool_result() 助手。",
        ),
        Question(
            prompt="为什么 todo/memory 这些「代理级工具」要被提前拦截，不走 registry.dispatch？",
            options=[
                "因为它们更快",
                "因为它们需要 per-agent 状态（如 _todo_store），注册表给不了",
                "因为它们不返回 JSON",
                "因为它们没有 schema",
            ],
            answer=1,
            explain="它们需要 per-agent 状态（_todo_store/_memory_store/clarify_callback），通过 kwargs 注入，注册表无法提供。",
        ),
    ],
    further_reading=[
        "tools/registry.py",
        "toolsets.py",
        "tools/todo_tool.py",
        "agent/agent_runtime_helpers.py",
    ],
)

# ---- 课 5：系统提示词 --------------------------------------------------- #
_L(
    5,
    "系统提示词（三层缓存友好结构）",
    "stable / context / volatile",
    [
        """# 第 5 课：系统提示词

系统提示词被装配成**三层**，顺序刻意为之（provider 缓存前缀，稳定内容放前最大化命中）：

| 层 | 内容 | 变化频率 |
|---|---|---|
| **stable** | 身份（SOUL.md）、任务完成指引、工具感知指引（仅当对应工具在 valid_tool_names 时注入 MEMORY_GUIDANCE 等） | 极少变 |
| **context** | 上下文文件（cwd 的 AGENTS.md/CLAUDE.md/.cursorrules）+ 调用方 system_message | 每项目不同 |
| **volatile** | 记忆快照、用户画像、外部记忆块、时间戳行（**只有日期，不到分钟**） | 每会话不同 |

## 关键约束

- **每会话只构建一次并缓存**（`agent._cached_system_prompt`）。除了上下文压缩后 `invalidate_system_prompt()` 重建，**永不重建**。
- 重建会让 Anthropic/OpenAI/OpenRouter 前缀缓存失效，**成本暴涨**。
- **插件上下文进 USER 消息，绝不进系统提示词**（见循环里的 `pre_llm_call` 钩子）。
- **改会话中工具集 / 重载记忆 / 重建系统提示词 = 破坏缓存 = 禁止**（压缩除外）。
- **时间戳只有日期**，不到分钟——保持当日 byte 稳定以保住 KV 缓存（PR #20451）。
- **工具感知指引是条件性的**：`MEMORY_GUIDANCE` 仅当 `"memory" in valid_tool_names` 时注入。所以禁用 toolset 会缩小提示词，但提示词仍按会话缓存。

```python
# agent/system_prompt.py（简化）
def build_system_prompt(agent, system_message=None) -> str:
    parts = build_system_prompt_parts(agent, system_message=system_message)
    return "\\n\\n".join(p for p in
        (parts["stable"], parts["context"], parts["volatile"]) if p)
```""",
    ],
    [
        Question(
            prompt="为什么系统提示词里的时间戳只有日期，不到分钟？",
            options=[
                "节省 token",
                "保持当日 byte 稳定，保住 provider 前缀缓存",
                "避免时区问题",
                "数据库限制",
            ],
            answer=1,
            explain="分钟级会让缓存每分钟失效一次，成本暴涨。date-only 让当日 byte 稳定（PR #20451）。",
        ),
        Question(
            prompt="插件想往上下文注入信息，正确做法是？",
            options=[
                "直接改系统提示词",
                "用 pre_llm_call 钩子注入到 USER 消息",
                "改 DEFAULT_CONFIG",
                "改 SOUL.md",
            ],
            answer=1,
            explain="系统提示词是 Hermes 的领地且必须缓存；插件上下文进 USER 消息以保住前缀缓存。",
        ),
    ],
    further_reading=[
        "agent/system_prompt.py",
        "agent/prompt_builder.py",
    ],
)

# ---- 课 6：会话存储 ----------------------------------------------------- #
_L(
    6,
    "会话存储（SessionDB + FTS5）",
    "SQLite / WAL / 全文搜索",
    [
        """# 第 6 课：会话存储

**位置**：`hermes_state.py`，存储 `~/.hermes/state.db`（SQLite，WAL 模式）。

## 表结构

- `sessions` —— id、source（cli/telegram/...）、model、system_prompt、parent_session_id（压缩链）、token 计数、cwd、title...
- `messages` —— id、session_id、role、content、tool_call_id、tool_calls、tool_name、token_count、reasoning 字段、active（软删/rewind）...
- `state_meta` —— key/value 内部状态
- `compression_locks` —— 每会话压缩锁
- **两个 FTS5 虚拟表**：unicode61 + trigram（后者服务 CJK）

## 关键点

- **`search_messages(query)`**：BM25 跨所有消息搜，带片段抽取、source/role 过滤。CJK 走 trigram 或 LIKE 兜底。
- **写入并发**：`_execute_write()` 用 `BEGIN IMMEDIATE` + 20–150ms 抖动重试（最多 15 次）打散 SQLite convoy。每 50 次写做一次 `wal_checkpoint(PASSIVE)`。
- **WAL 兜底**：NFS/SMB/FUSE 会触发 "locking protocol" 错误，`apply_wal_with_fallback()` 回退 `DELETE` 模式，**每 (process, db_label) 只告警一次**避免刷爆日志。
- **schema 演进**：`SCHEMA_VERSION = 14`，但**加列不需要 bump**——`_reconcile_columns()` 声明式 diff 并自动补齐。只在重命名/重构时才 bump。
- **删除会话**：把子会话的 `parent_session_id` 置 NULL（而非级联），分支/子代理转写得以幸存。

> 测试时绝不能写 `~/.hermes/`——`tests/conftest.py` 的 `_isolate_hermes_home` autouse fixture 把 `HERMES_HOME` 重定向到临时目录。""",
    ],
    [
        Question(
            prompt="SessionDB 用什么全文搜索引擎？",
            options=["Whoosh", "FTS5（SQLite）", "Elasticsearch", "Tantivy"],
            answer=1,
            explain="SQLite 内建的 FTS5，配 unicode61 + trigram 两个虚拟表（trigram 服务 CJK）。",
        ),
        Question(
            prompt="往 state.db 加一列需要 bump SCHEMA_VERSION 吗？",
            options=[
                "需要",
                "不需要，_reconcile_columns() 声明式自动补齐",
                "需要，且要写迁移脚本",
                "取决于列类型",
            ],
            answer=1,
            explain="加列由 _reconcile_columns() 自动处理；只在重命名/重构时才 bump 版本。",
        ),
    ],
    further_reading=[
        "hermes_state.py",
    ],
)

# ---- 课 7：记忆系统 ----------------------------------------------------- #
_L(
    7,
    "记忆系统（Memory）",
    "Provider ABC + Manager 编排",
    [
        """# 第 7 课：记忆系统

**位置**：`agent/memory_provider.py`（ABC）、`agent/memory_manager.py`（编排器）、`plugins/memory/<name>/`（提供者）。

## MemoryProvider ABC

```python
class MemoryProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def is_available(self) -> bool: ...
    @abstractmethod
    def initialize(self, session_id, **kwargs) -> None: ...  # 总是收到 hermes_home
    def prefetch(self, query, *, session_id="") -> str: return ""
    def sync_turn(self, user_content, assistant_content, *, session_id="", messages=None) -> None: ...
    @abstractmethod
    def get_tool_schemas(self) -> list: ...
    def shutdown(self) -> None: ...
    # 可选钩子：on_turn_start / on_session_switch / on_pre_compress
    #           / on_delegation / on_memory_write / get_config_schema
```

## MemoryManager

- 编排**内置提供者 + 至多一个外部提供者**。`add_provider()` 拒绝第二个外部。
- `handle_tool_call(tool_name, args)` 通过 `_tool_to_provider` 索引路由。
- 每轮：`prefetch_all(user_msg)` → 注入上下文；轮后 `sync_all(...)` → `queue_prefetch_all(...)` 为下一轮预取。

## 关键点

- **`initialize()` 总是收到 `hermes_home`** kwarg——提供者必须用它做 profile 隔离存储，**禁止** `Path.home()/".hermes"`。
- **`agent_context="cron"` 时跳过写入**——cron 系统提示词会污染用户画像。
- **`on_session_switch(reset=False)` 在压缩时触发**，让提供者刷新缓存状态而不重新初始化。
- **政策（2026-05）**：**不再接受新 in-tree 记忆提供者**。现有 `plugins/memory/` 集合关闭；新后端必须作为**独立插件仓库**发布到 `~/.hermes/plugins/`。
- 记忆内容被包进 `<memory-context>` 围栏并标注为「参考数据，非新用户输入」，`StreamingContextScrubber` 在流式时跨 chunk 剥离这些标签。""",
    ],
    [
        Question(
            prompt="MemoryManager 最多能接几个外部记忆提供者？",
            options=["无限制", "1 个", "3 个", "取决于配置"],
            answer=1,
            explain="内置 1 个 + 至多 1 个外部。add_provider() 拒绝第二个外部，防 schema 膨胀和后端冲突。",
        ),
        Question(
            prompt="关于「新记忆提供者」的政策是？",
            options=[
                "可继续往 plugins/memory/ 加",
                "不再接受 in-tree 新提供者，必须发独立插件仓库",
                "必须改 run_agent.py",
                "需 bump config 版本",
            ],
            answer=1,
            explain="2026-05 政策：plugins/memory/ 集合关闭，新后端作为独立插件仓库发布到 ~/.hermes/plugins/。",
        ),
    ],
    further_reading=[
        "agent/memory_provider.py",
        "agent/memory_manager.py",
    ],
)

# ---- 课 8：配置系统 ----------------------------------------------------- #
_L(
    8,
    "配置系统（三个 Loader）",
    "CLI / 子命令 / Gateway 直读",
    [
        """# 第 8 课：配置系统

**必须知道自己在哪条 loader 上**：

| Loader | 使用者 | 位置 |
|---|---|---|
| `load_cli_config()` | CLI 模式（`hermes chat`） | `cli.py` |
| `load_config()` | `hermes tools`/`hermes setup`/多数子命令 | `hermes_cli/config.py` |
| 直接 YAML 读 | Gateway 运行时 | `gateway/run.py` + `gateway/config.py` |

**症状诊断**：加了新 key，CLI 看得到但 Gateway 看不到（或反之）→ 走错了 loader。检查 `DEFAULT_CONFIG` 覆盖面。

## 关键点

- `DEFAULT_CONFIG` 带 `_config_version`（当前 25）。**只在主动迁移（重命名/重构）时才 bump**；往现有 section 加 key 由深合并自动处理，**不需要 bump**。
- `OPTIONAL_ENV_VARS` 是 `.env` 变量元数据（描述/prompt/url/password/category）。**`.env` 只放密钥**；非密钥设置（超时、阈值、路径、显示偏好）属于 `config.yaml`。
- 缓存键是 `(path, mtime_ns, size)`，`save_config()` 用 `atomic_yaml_write`（新 inode）让 stat 看到新 mtime → 缓存自动失效。
- `_ENV_VAR_NAME_DENYLIST`：dashboard 写入器绝不能写的变量（LD_PRELOAD/PYTHONPATH/HERMES_HOME……），防 RCE。
- `_CONFIG_LOCK = threading.RLock()`：libyaml C 扩展并发 `safe_load` 不安全，所有读写串行。

## 三个 loader 之外的「直接 env 桥接」

某些 config 键会被代码桥接成 env var 供子进程用，例如 `terminal.cwd` → `TERMINAL_CWD`。`MESSAGING_CWD` 已移除。""",
    ],
    [
        Question(
            prompt="加了新 config key，CLI 能看到但 Gateway 看不到，最可能原因？",
            options=[
                "忘了 bump _config_version",
                "走错了 loader，Gateway 用直接 YAML 读",
                "config.yaml 损坏",
                "DEFAULT_CONFIG 缺少该 section",
            ],
            answer=1,
            explain="三条 loader 路径不同。Gateway 运行时直接读 YAML，不走 load_config() 的深合并。检查 DEFAULT_CONFIG 覆盖面。",
        ),
        Question(
            prompt="往现有 section 加一个新 key，需要 bump _config_version 吗？",
            options=["需要", "不需要，深合并自动处理", "取决于 key 类型", "需要写迁移脚本"],
            answer=1,
            explain="加 key 由 _deep_merge 自动处理；只在重命名/重构（主动迁移）时才 bump。",
        ),
    ],
    further_reading=[
        "hermes_cli/config.py",
        "cli.py",
    ],
)

# ---- 课 9：Profile 与路径安全 ------------------------------------------- #
_L(
    9,
    "Profile 隔离与路径安全",
    "get_hermes_home / 多实例",
    [
        """# 第 9 课：Profile 隔离与路径安全

Hermes 支持 **profile**——多个完全隔离的实例，各有自己的 `HERMES_HOME`（config、密钥、记忆、会话、技能、gateway……）。

## 核心机制

`hermes_cli/main.py::_apply_profile_override()` 在**任何 hermes 模块 import 之前**解析 `--profile`/`-p` 并设 `HERMES_HOME`。所有 `get_hermes_home()` 引用自动 scope 到当前 profile。

## 规则（profile-safe 代码）

1. **用 `get_hermes_home()` 做所有 HERMES_HOME 路径**（从 `hermes_constants` import）。**绝不**硬编码 `~/.hermes` 或 `Path.home()/".hermes"`。

```python
# GOOD
from hermes_constants import get_hermes_home, display_hermes_home
config_path = get_hermes_home() / "config.yaml"
print(f"Config saved to {display_hermes_home()}/config.yaml")

# BAD —— 破坏 profile
config_path = Path.home() / ".hermes" / "config.yaml"
```

2. **`display_hermes_home()` 用于用户消息**（默认返回 `~/.hermes`，profile 模式返回 `~/.hermes/profiles/<name>`）。

3. **模块级常量是安全的**——它们在 import 时缓存 `get_hermes_home()`，而 import 发生在 `_apply_profile_override()` 设 env 之后。

4. **测试 mock `Path.home()` 时也要设 `HERMES_HOME`**——因为代码读 env var 不只读 `Path.home()`：

```python
with patch.object(Path, "home", return_value=tmp_path), \\
     patch.dict(os.environ, {"HERMES_HOME": str(tmp_path / ".hermes")}):
    ...
```

5. **平台适配器用 token 锁**——用唯一凭证连接的适配器在 `connect()` 调 `acquire_scoped_lock()`，`disconnect()` 调 `release_scoped_lock()`，防两 profile 抢同一凭证。见 `gateway/platforms/telegram.py`。

6. **profile 操作是 HOME-anchored，不是 HERMES_HOME-anchored**——`_get_profiles_root()` 返回 `Path.home()/".hermes"/"profiles"`，让 `hermes -p coder profile list` 能看到所有 profile。

> 硬编码 `~/.hermes` 是 PR #3575 修的 5 个 bug 的根源。""",
    ],
    [
        Question(
            prompt="代码里读取状态文件路径，正确写法是？",
            options=[
                "Path.home() / '.hermes' / 'state.db'",
                "get_hermes_home() / 'state.db'",
                "'~/.hermes/state.db'",
                "os.path.expanduser('~/.hermes/state.db')",
            ],
            answer=1,
            explain="get_hermes_home() 读 HERMES_HOME env var，自动 scope 到当前 profile。硬编码会破坏 profile 隔离。",
        ),
        Question(
            prompt="为什么 _apply_profile_override() 必须在任何 hermes 模块 import 之前跑？",
            options=[
                "为了性能",
                "因为模块在 import 时缓存 get_hermes_home()，必须先设好 env",
                "避免循环 import",
                "libyaml 要求",
            ],
            answer=1,
            explain="模块级常量在 import 时缓存 HERMES_HOME；若 override 在后，缓存的就是错误路径。",
        ),
    ],
    further_reading=[
        "hermes_constants.py",
        "hermes_cli/main.py",
    ],
)

# ---- 课 10：CLI 与斜杠命令 --------------------------------------------- #
_L(
    10,
    "CLI 与斜杠命令注册",
    "COMMAND_REGISTRY 单一真相源",
    [
        """# 第 10 课：CLI 与斜杠命令

## 核心设计

所有斜杠命令定义在**单一真相源** `COMMAND_REGISTRY`（`CommandDef` 列表，`hermes_cli/commands.py`）。所有下游消费者自动派生：

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

## CommandDef 字段

- `name` —— 规范名（不带斜杠）
- `description` —— 人类可读
- `category` —— Session / Configuration / Tools & Skills / Info / Exit
- `aliases` —— 别名元组
- `args_hint` —— 参数占位（`<prompt>` / `[name]`）
- `subcommands` —— 可补全的子命令
- `cli_only` —— 仅 CLI
- `gateway_only` —— 仅 gateway
- `gateway_config_gate` —— 配置 dotpath，为真时 `cli_only` 命令在 gateway 也可用

## 加一条斜杠命令

1. 在 `COMMAND_REGISTRY` 加 `CommandDef(...)`。
2. 在 `cli.py` 的 `process_command()` 加 `elif canonical == "mycommand": self._handle_mycommand(...)`。
3. 若 gateway 可用，在 `gateway/run.py` 加 handler。
4. 持久设置用 `save_config_value()`。

**加别名**只改 `aliases` 元组——派发、帮助、菜单、自动补全自动更新。

## KawaiiSpinner

API 调用时的可爱颜文字动画。皮肤可覆盖脸/动词/翅膀。**绝不用 `\\033[K`**（在 `prompt_toolkit.patch_stdout` 下泄漏成字面 `?[K`），用空格填充 `f"\\r{line}{' ' * pad}"`。

## 新交互菜单

必须用 `hermes_cli/curses_ui.py`（`curses_radiolist`/`curses_checklist`）——`simple_term_menu` 在 tmux/iTerm2 重影，仅遗留兜底。""",
    ],
    [
        Question(
            prompt="加一个斜杠命令的别名，需要改几处？",
            options=["1 处（CommandDef 的 aliases 元组）", "2 处", "3 处", "每个下游消费者都要改"],
            answer=0,
            explain="只改 aliases 元组，派发/帮助/菜单/自动补全/Telegram/Slack/Discord 全部自动更新。这是 COMMAND_REGISTRY 设计的精髓。",
        ),
        Question(
            prompt="为什么 spinner/display 代码绝不能用 `\\033[K`？",
            options=[
                "ANSI 标准不支持",
                "在 prompt_toolkit.patch_stdout 下泄漏成字面 ?[K 文本",
                "终端不支持颜色",
                "和 Rich 冲突",
            ],
            answer=1,
            explain="会泄漏成字面 ?[K 文本。应改用空格填充：回车加内容再加空格补齐行宽。",
        ),
    ],
    further_reading=[
        "hermes_cli/commands.py",
        "cli.py",
        "agent/display.py",
    ],
)

# ---- 课 11：Gateway 与平台适配器 ---------------------------------------- #
_L(
    11,
    "Gateway 与平台适配器",
    "双消息守卫 / AIAgent 缓存",
    [
        """# 第 11 课：Gateway 与平台适配器

**位置**：`gateway/run.py`（`GatewayRunner`）、`gateway/platforms/base.py`（`BasePlatformAdapter`）。

## 消息流（以 Telegram 为例）

1. PTB 轮询收到 update → `TelegramAdapter` 建 `MessageEvent` → 调 `handle_message()`。
2. **守卫 #1（base adapter）**：检查 `session_key in _active_sessions`：
   - 活跃 → 合并进 `_pending_messages[session_key]`（单槽，最新者胜）或交给 `_busy_session_handler`（busy-input 模式：interrupt/queue/steer）。
   - 空闲 → 获取守卫（`_active_sessions[key] = asyncio.Event()`），spawn `_process_message_background()`。
3. **守卫 #2（gateway runner）**：`_process_message_background()` 里检查 `should_bypass_active_session()`——识别出的命令（`/stop`/`/new`/`/queue`/`/status`/`/approve`/`/deny` 等）**inline 派发**，绕开运行中的 agent。
4. 常规消息：取/建缓存 AIAgent → `run_conversation()` → 流式投递 → 最终回复。
5. 完成：`finally` 释放守卫，检查 `_pending_messages` 有无排队后续。

## 两个守卫都必须放行控制命令

任何要在 agent 阻塞时抵达 runner 的新命令必须**同时绕过两个守卫**并 inline 派发，**不能**走 `_process_message_background()`（会与 session 生命周期竞争）。

## AIAgent 缓存

`OrderedDict` LRU，max 128，空闲 TTL 1h。**绝不能**每条消息新建 AIAgent——会重建系统提示词，破坏前缀缓存（Anthropic 上约 10x 成本）。

## Scoped lock

用唯一凭证连接的适配器（bot token、API key）**必须**在 `connect()` 调 `acquire_scoped_lock()`、`disconnect()` 调 `release_scoped_lock()`，防两 profile 抢同一凭证。见 `gateway/platforms/telegram.py`。

## 后台进程通知

`terminal(background=true, notify_on_complete=true)` 时 gateway 跑 watcher 检测完成并触发新 agent 轮。详略由 `display.background_process_notifications` 控制（`all`/`result`/`error`/`off`）。""",
    ],
    [
        Question(
            prompt="Gateway 有几个消息守卫？",
            options=["1 个", "2 个", "3 个", "取决于平台"],
            answer=1,
            explain="两个：(1) base adapter 的 _active_sessions + _pending_messages；(2) runner 的 should_bypass_active_session + /stop 等拦截。",
        ),
        Question(
            prompt="为什么 Gateway 不能每条消息新建一个 AIAgent？",
            options=[
                "内存不够",
                "会重建系统提示词，破坏前缀缓存（约 10x 成本）",
                "线程不安全",
                "SQLite 锁冲突",
            ],
            answer=1,
            explain="AIAgent 缓存（OrderedDict LRU）保住 prompt 缓存。新建会重建系统提示词，Anthropic 上成本约 10x。",
        ),
    ],
    further_reading=[
        "gateway/run.py",
        "gateway/platforms/base.py",
        "gateway/platforms/telegram.py",
    ],
)

# ---- 课 12：插件系统 --------------------------------------------------- #
_L(
    12,
    "插件系统",
    "通用插件 / 模型 provider 插件",
    [
        """# 第 12 课：插件系统

## 通用插件（`hermes_cli/plugins.py` + `plugins/<name>/`）

**发现源**（后者覆盖前者）：bundled `<repo>/plugins/` → 用户 `~/.hermes/plugins/` → 项目 `./.hermes/plugins/`（需 `HERMES_ENABLE_PROJECT_PLUGINS`）→ pip entry-points（`hermes_agent.plugins` 组）。

`PluginContext` 让插件 `register(ctx)` 能：
- 注册**生命周期钩子**：`pre_tool_call`/`post_tool_call`/`pre_llm_call`/`post_llm_call`/`on_session_start`/`on_session_end`/`transform_terminal_output`/`transform_tool_result`/`transform_llm_output` 等。
- `ctx.register_tool(...)` 注册工具。
- `ctx.register_cli_command(...)` 注册 CLI 子命令（自动接入 `hermes <plugin> <subcmd>`）。
- `ctx.register_skill(...)` / `register_context_engine(...)` / `register_image_gen_provider(...)` / `.llm` 属性。

## 模型 provider 插件（`plugins/model-providers/<name>/`）

单独的**懒发现**系统。每个 `__init__.py` 调 `providers.register_provider(ProviderProfile(...))`。

扫描顺序：bundled → user → legacy `providers/<name>.py`。**user 同名覆盖 bundled**——第三方无需改仓库即可替换内置 profile。

## 关键规则

- **插件绝不能改核心文件**（`run_agent.py`/`cli.py`/`gateway/run.py`/`hermes_cli/main.py`）。需要新能力就**扩展通用插件面**（新钩子 / 新 ctx 方法），绝不硬编码插件逻辑进核心。
- **发现时机陷阱**：`discover_plugins()` 只是 `import model_tools.py` 的副作用。读插件状态但没先 import `model_tools` 的代码路径**必须显式调** `discover_plugins()`（幂等）。
- **`memory/`/`context_engine/`/`platforms/`/`model-providers/` 被顶层扫描器跳过**——它们有自己的发现系统。
- **插件工具 `override=True`** 可替换同名内置工具；不加则跨 toolset 名字冲突被拒。
- **`HERMES_PLUGINS_DEBUG=1`** 把插件发现日志 tee 到 stderr。

## 最小插件示例

`plugin.yaml`:
```yaml
name: spotify
version: 1.0.0
description: "Native Spotify integration..."
author: NousResearch
kind: backend
provides_tools: [spotify_playback, spotify_search]
```
`__init__.py`:
```python
def register(ctx):
    ctx.register_tool(
        name="spotify_playback",
        toolset="spotify",
        schema={...},
        handler=_handle,
        requires_env=["SPOTIFY_CLIENT_ID"],
    )
```""",
    ],
    [
        Question(
            prompt="插件想加新能力，但核心没暴露对应钩子，正确做法是？",
            options=[
                "改 run_agent.py",
                "改 cli.py",
                "扩展通用插件面（加新钩子/新 ctx 方法）",
                "fork 仓库",
            ],
            answer=2,
            explain="插件绝不能改核心文件。要新能力就扩展通用插件面，绝不硬编码插件逻辑进核心（PR #5295 清了 95 行硬编码）。",
        ),
        Question(
            prompt="用户目录的模型 provider 插件和 bundled 同名时？",
            options=[
                "报错",
                "bundled 优先",
                "user 覆盖 bundled（last-writer-wins）",
                "随机选一个",
            ],
            answer=2,
            explain="register_provider() last-writer-wins，user 后扫描故覆盖 bundled。第三方无需改仓库即可替换内置 profile。",
        ),
    ],
    further_reading=[
        "hermes_cli/plugins.py",
        "providers/__init__.py",
    ],
)

# ---- 课 13：技能 / Cron / 委派 / Kanban --------------------------------- #
_L(
    13,
    "技能 / Cron / 委派 / Kanban",
    "过程性记忆与多代理协作",
    [
        """# 第 13 课：技能 / Cron / 委派 / Kanban

## 技能（Skills）

- **技能 = 过程性记忆**：一份 `SKILL.md`（带 frontmatter）+ 可选 `scripts/`/`references/`/`templates/`。
- **激活**：用户输入 `/<skill-name>`。被作为 **USER 消息**注入（不是系统提示词），以**保住前缀缓存**。
- **硬标准**：`description` ≤ 60 字符；正文提到的工具必须是原生 Hermes 工具（`` `terminal` ``、`` `web_extract` ``、`` `read_file` ``、`` `patch` ``、`` `search_files` ``）；`platforms:` 门控对照脚本实际 import 审计；`author` 先署人类。
- 现代 section 顺序：When to Use → Prerequisites → How to Run → Quick Reference → Procedure → Pitfalls → Verification。

## Cron

- 调度格式：时长（`30m`/`2h`）、"every" 短语、5 字段 cron、ISO 时间戳。
- `tick()` 用文件锁防跨进程重复；**先推进 `next_run_at` 再执行**（at-most-once）。
- catchup 窗口 = 周期一半，钳制 120s–2h。
- **cron 会话默认 `skip_memory=True`**——记忆提供者在 cron 期间不跑。
- cron 投递**不镜像**进目标 gateway 会话——落到自己的 cron 会话。
- 不活跃超时默认 600s（`HERMES_CRON_TIMEOUT`）。

## 委派（Delegation / 子代理）

- `delegate_task` 派生隔离子代理（独立上下文 + 终端会话）。**同步**：父等子摘要；父被中断则子取消。
- **单** vs **批量（并行）**，并发上限 `delegation.max_concurrent_children`（默认 3）。
- 角色：`leaf`（默认，专注 worker，不能调 delegate_task/clarify/memory/send_message/execute_code）；`orchestrator`（保留 delegate_task，深度上限 `max_spawn_depth` 默认 2）。
- **`delegate_task` 不持久**。长跑且跨轮的工作用 `cronjob` 或 `terminal(background=True, notify_on_complete=True)`。
- **模型给的 `max_iterations` 被忽略**——config 值权威。
- **`_last_resolved_tool_names` 是进程全局**——`_run_single_child` 保存/恢复它；新代码要知道它在子代理跑期间可能 stale。

## Kanban

- 持久 SQLite 看板，多 profile/worker 协作。
- **隔离模型**：Board 是硬边界（`HERMES_KANBAN_BOARD` 锁定）；Tenant 是 board 内软命名空间。
- worker toolset（8 工具）+ orchestrator toolset（额外 2）。**不在 kanban 任务时 schema 占用为零**。
- dispatcher 默认跑在 gateway 内（`kanban.dispatch_in_gateway: true`），每 60s tick。
- 连续 `failure_limit` 次（默认 2）非成功自动 block，防空转。
- worker 任务归属强制——防 prompt 注入的 worker 破坏兄弟运行。""",
    ],
    [
        Question(
            prompt="技能被激活时，内容注入到哪里？",
            options=[
                "系统提示词",
                "USER 消息",
                "tool 结果",
                "config.yaml",
            ],
            answer=1,
            explain="作为 USER 消息注入以保住前缀缓存。这是规范模式——系统提示词不能动。",
        ),
        Question(
            prompt="delegate_task 的「同步」含义是？",
            options=[
                "父不等子",
                "父等子摘要再继续；父被中断则子取消",
                "子和父跑在同一进程",
                "子必须先完成才能发起新父",
            ],
            answer=1,
            explain="同步：父阻塞等子摘要。长跑且跨轮的工作用 cronjob 或 terminal(background=True)。",
        ),
        Question(
            prompt="cron 会话默认 `skip_memory=True` 的原因是？",
            options=[
                "节省 token",
                "避免记忆提供者污染用户画像",
                "SQLite 锁冲突",
                "提速",
            ],
            answer=1,
            explain="cron 系统提示词若被记忆写入会污染用户画像。所以记忆提供者在 cron 期间不跑。",
        ),
    ],
    further_reading=[
        "agent/skill_commands.py",
        "cron/scheduler.py",
        "tools/delegate_tool.py",
        "hermes_cli/kanban.py",
    ],
)

# ---- 课 14：上下文压缩 ------------------------------------------------- #
_L(
    14,
    "上下文压缩",
    "唯一允许的上下文突变",
    [
        """# 第 14 课：上下文压缩

> 这是**唯一允许**中途改过去上下文的场景（AGENTS.md 明示）。其他地方破坏 prompt 缓存 = 禁止。

## 流程（compress_context）

1. **懒可行性检查**：首次尝试时 `check_compression_model_feasibility(agent)`，aux 模型上下文窗 < 主阈值则告警并自动降低会话阈值。
2. **压缩锁**（`state.db` 的 `compression_locks` 表，持锁者 id = `pid:tid:agent:uuid`）：防两个共享 session_id 的 AIAgent 同时轮转。锁子系统缺失时**fail-open**（宁可冒险也不无限空转）。
3. **通知记忆提供者** `on_pre_compress(messages)`——在丢弃前抽取洞察。
4. **压缩**：用 aux（便宜快）模型摘要中段，保护头尾。token 预算尾部保护（非固定消息数）。LLM 摘要前先做工具输出裁剪。失败则返回 messages 不变，会话不轮转。
5. **会话切分 + 轮转**（仅成功时）：`end_session(old, "compression")` → 新 `session_id`（`parent_session_id = old`）→ `create_session` → 重建系统提示词 → 通知上下文引擎 `on_session_start(boundary_reason="compression")` → 通知记忆提供者 `on_session_switch(reset=False, reason="compression")` → 清文件去重缓存。
6. 连续压缩 ≥2 次会告警（质量递减）。

## SUMMARY_PREFIX 是承重提示工程

标注摘要为「参考背景，非活动指令」，让模型只回最新 user 消息，在最新消息偏离时丢弃过期的 `## Active Task`，并明示系统提示词里的持久记忆（MEMORY.md/USER.md）**永远**权威。改它要把旧版加进 `_HISTORICAL_SUMMARY_PREFIXES` 以便再规范化时剥离残留指令。

## `/compress` 命令

用 `force=True` 绕过摘要失败冷却，可立即重试。自动压缩用 `False`。""",
    ],
    [
        Question(
            prompt="Hermes 里唯一允许中途改过去上下文的场景是？",
            options=[
                "记忆 nudge",
                "上下文压缩",
                "技能激活",
                "profile 切换",
            ],
            answer=1,
            explain="压缩是唯一例外。其他地方改过去上下文 / 改会话中工具集 / 重载记忆 = 破坏 prompt 缓存 = 禁止。",
        ),
        Question(
            prompt="压缩锁子系统缺失时，compress_context 的行为是？",
            options=[
                "抛异常",
                "无限重试",
                "fail-open（宁可冒险也不无限空转）",
                "回退到不压缩",
            ],
            answer=2,
            explain="fail-open：一个无限不压缩的空转循环比罕见并发压缩风险更糟。",
        ),
    ],
    further_reading=[
        "agent/context_compressor.py",
        "agent/conversation_compression.py",
    ],
)

# ---- 课 15：如何扩展 + 关键陷阱 ----------------------------------------- #
_L(
    15,
    "如何扩展 Hermes & 关键陷阱",
    "工具/命令/技能/插件 + 必读约定",
    [
        """# 第 15 课：如何扩展 & 关键陷阱

## 添加工具（首选插件路由）

`~/.hermes/plugins/mytool/plugin.yaml` + `__init__.py` 里 `ctx.register_tool(...)`。免改 `tools/` 和 `toolsets.py`，可启停。

**内置路由**（贡献核心工具时）：创建 `tools/your_tool.py`（模块级 `registry.register()`）+ 加入 `toolsets.py` 的 `_HERMES_CORE_TOOLS` 或新 toolset。**接线步骤必须**——自动发现只让 schema 可查。

handler 规则：
- 签名 `(args, **kwargs) -> str`，必须返回 JSON 字符串。
- 持久状态用 `get_hermes_home()`，绝不 `Path.home()/".hermes"`。
- schema 描述里提文件路径用 `display_hermes_home()`。
- **禁止**硬编码跨 toolset 工具名引用（可能不可用导致幻觉）；需要的话在 `get_tool_definitions()` 动态加。

## 添加斜杠命令

1. `hermes_cli/commands.py` 的 `COMMAND_REGISTRY` 加 `CommandDef(...)`。
2. `cli.py` 的 `process_command()` 加 handler。
3. gateway 可用则加 `gateway/run.py` handler。
4. 持久设置用 `save_config_value()`。加别名只改 `aliases`。

## 添加配置

`config.yaml` 新 key → 加到 `DEFAULT_CONFIG`。往现有 section 加 key **不需要** bump `_config_version`；重命名/重构才 bump。

## 关键陷阱速查

| 规则 | 为什么 |
|---|---|
| 用 `get_hermes_home()`，绝不硬编码 `~/.hermes` | 破坏 profile 隔离 |
| 测试要同时 mock `Path.home()` 和设 `HERMES_HOME` | 代码读 env var |
| prompt 缓存不能破（不改过去上下文/会话中工具集/重建系统提示词） | 成本暴涨 |
| spinner 绝不用 `\\033[K` | 在 patch_stdout 下泄漏 |
| 新菜单用 `curses_ui.py` | simple_term_menu 重影 |
| gateway 两守卫，控制命令要同时绕过并 inline 派发 | 否则与 session 生命周期竞争 |
| `_last_resolved_tool_names` 是进程全局，子代理期间可能 stale | delegate_tool 保存/恢复它 |
| schema 描述禁止跨 toolset 工具名引用 | 可能不可用导致幻觉 |
| handler 必须返回 JSON 字符串 | registry 不包装返回值 |
| `delegate_task` 不持久 | 长跑用 cronjob 或 terminal(background=True) |
| 不再接受新 in-tree 记忆提供者 | 发独立插件仓库 |
| 插件绝不能改核心文件 | 扩展通用插件面 |
| 测试不写 `~/.hermes/` | _isolate_hermes_home 重定向 |
| 用 `scripts/run_tests.sh` 别直接 pytest | CI 对等 |
| 依赖必须有上界 | 防供应链攻击 |
| 别写 change-detector 测试 | 测行为契约不测数据快照 |""",
    ],
    [
        Question(
            prompt="新增一个核心工具时，下列哪步是「必须但常被忘」的？",
            options=[
                "写 handler",
                "在 toolsets.py 把工具名加进 _HERMES_CORE_TOOLS 或某 toolset",
                "写 check_fn",
                "加 emoji",
            ],
            answer=1,
            explain="自动发现只让 schema 可查；工具必须出现在 toolset 解析后的 tools 列表里才暴露给模型。这步是手工的。",
        ),
        Question(
            prompt="下列哪个是「change-detector 测试」（应避免）？",
            options=[
                "断言 catalog 里每个模型都有 context-length 条目",
                "断言 _config_version == 25",
                "断言迁移后用户版本 == 当前最新",
                "断言 plan-only 模型不泄漏进 legacy 列表",
            ],
            answer=1,
            explain="快照当前数据（版本号/枚举数/模型名）的测试每次数据更新就坏。应测行为契约（关系/不变量）。",
        ),
        Question(
            prompt="依赖版本约束的正确写法（post-1.0 包）？",
            options=["`>=0.28.1`（无上界）", "`>=1.5.0,<2`", "`==1.5.0`", "`>=1.5.0`"],
            answer=1,
            explain="post-1.0 用 `>=floor,<next_major`；pre-1.0 用 `<0.(minor+2)`；CI-only 用 `==exact`。绝不裸 `>=X.Y.Z`（供应链攻击面）。",
        ),
    ],
    further_reading=[
        "docs/getting-started-learning-guide.md",
        "AGENTS.md",
    ],
)


# --------------------------------------------------------------------------- #
# 渲染辅助
# --------------------------------------------------------------------------- #


def _wrap(text: str, width: int = 78) -> str:
    """简单换行：保留代码块（``` 围栏内）原样，其余按宽度折行。"""
    if width <= 0:
        return text
    lines = text.split("\n")
    out = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # 简单折行：超长且无空格的（如表格行）保留；其余按词折行
        if len(line) <= width or line.strip() == "":
            out.append(line)
            continue
        # 粗略折行
        words = line.split(" ")
        cur = ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > width:
                out.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            out.append(cur)
    return "\n".join(out)


def _hr(char: str = "─", n: int = 72) -> str:
    return dim(char * n)


def _pager_hint(page_idx: int, total: int) -> str:
    return dim(f"[ 第 {page_idx + 1}/{total} 页 ]  Enter=下一页  p=上一页  m=菜单  q=退出")


# --------------------------------------------------------------------------- #
# 进度
# --------------------------------------------------------------------------- #


def _load_progress() -> dict:
    if PROGRESS_PATH.exists():
        try:
            return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_progress(data: dict) -> None:
    try:
        PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _quiz_key(lid: int) -> str:
    return f"lesson_{lid}"


def _lesson_done(data: dict, lid: int) -> bool:
    rec = data.get(_quiz_key(lid), {})
    return bool(rec.get("passed"))


def _best_score(data: dict, lid: int) -> Optional[int]:
    rec = data.get(_quiz_key(lid), {})
    return rec.get("best")


def _record_result(data: dict, lid: int, score: int, total: int) -> None:
    key = _quiz_key(lid)
    rec = data.get(key, {})
    rec["last"] = score
    rec["total"] = total
    prev_best = rec.get("best", -1)
    rec["best"] = max(prev_best, score)
    rec["passed"] = score == total and total > 0
    data[key] = rec


# --------------------------------------------------------------------------- #
# 输入处理
# --------------------------------------------------------------------------- #


def _prompt(text: str = "") -> str:
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "q"


def _parse_answer(raw: str, n_options: int) -> Optional[int]:
    """接受 '1' / 'a' / 'A' / 选项文本片段。返回索引或 None。"""
    if not raw:
        return None
    s = raw.strip().lower()
    if s in ("q", "quit", "exit"):
        return None
    if s.isdigit():
        idx = int(s) - 1
        if 0 <= idx < n_options:
            return idx
        return None
    if len(s) == 1 and "a" <= s <= "z":
        idx = ord(s) - ord("a")
        if 0 <= idx < n_options:
            return idx
    return None


# --------------------------------------------------------------------------- #
# 课程渲染
# --------------------------------------------------------------------------- #


def _print_page(lesson: Lesson, idx: int) -> None:
    total = len(lesson.pages)
    print()
    print(_hr("="))
    print(bold(f"课程 {lesson.id}：{lesson.title}"))
    print(_hr("="))
    print()
    print(_wrap(lesson.pages[idx]))
    print()
    if idx < total - 1:
        print(_pager_hint(idx, total))
    else:
        print(dim("[ 最后一页 ]  Enter=开始测验  p=上一页  m=菜单  q=退出"))


def _run_quiz(lesson: Lesson) -> int:
    if not lesson.questions:
        print()
        print(yellow("本课没有测验题。"))
        _ = _prompt(dim("按 Enter 继续..."))
        return 0
    print()
    print(_hr("="))
    print(bold(f"随堂测验：{lesson.title}"))
    print(_hr("="))
    score = 0
    total = len(lesson.questions)
    for qi, q in enumerate(lesson.questions, 1):
        print()
        print(cyan(f"Q{qi}/{total}: {q.prompt}"))
        for oi, opt in enumerate(q.options):
            print(f"  {bold(str(oi + 1))}. {opt}")
        print()
        raw = _prompt(yellow("你的答案（输入序号）: "))
        ans = _parse_answer(raw, len(q.options))
        if raw.lower() in ("q", "quit", "exit"):
            print(dim("退出测验。"))
            return -1
        if ans is None:
            print(red("  ✗ 无效输入，记为错误。"))
        elif ans == q.answer:
            print(green("  ✓ 正确！"))
            score += 1
        else:
            correct = q.options[q.answer]
            print(red(f"  ✗ 错误。正确答案：{q.answer + 1}. {correct}"))
        if q.explain:
            print(dim(f"  解释：{q.explain}"))
    print()
    print(_hr("-"))
    pct = int(score / total * 100) if total else 0
    mark = green("棒！") if score == total else (yellow("加油！") if pct >= 60 else red("再看看？"))
    print(f"{bold('测验得分')}：{score}/{total}  ({pct}%)  {mark}")
    print(_hr("-"))
    return score


def _run_lesson(lesson: Lesson, data: dict) -> None:
    idx = 0
    total = len(lesson.pages)
    while True:
        _print_page(lesson, idx)
        cmd = _prompt(dim("> ")).lower()
        if cmd in ("q", "quit", "exit"):
            print(dim("退出。"))
            _save_progress(data)
            sys.exit(0)
        if cmd in ("m", "menu", "back"):
            return
        if cmd in ("r", "retry", "quiz"):
            score = _run_quiz(lesson)
            if score >= 0:
                _record_result(data, lesson.id, score, len(lesson.questions))
                _save_progress(data)
            continue
        if cmd in ("", "n", "next", " "):
            if idx < total - 1:
                idx += 1
            else:
                score = _run_quiz(lesson)
                if score >= 0:
                    _record_result(data, lesson.id, score, len(lesson.questions))
                    _save_progress(data)
                # 测验后回菜单
                return
            continue
        if cmd in ("p", "prev", "back"):
            if idx > 0:
                idx -= 1
            continue
        if cmd in ("h", "help", "?"):
            print(dim("命令：Enter/n=下一页  p=上一页  m=菜单  r=重测  q=退出"))
            continue
        print(dim("未知命令。Enter=下一页  m=菜单  q=退出"))


# --------------------------------------------------------------------------- #
# 菜单
# --------------------------------------------------------------------------- #


def _print_banner() -> None:
    print()
    print(_hr("="))
    print(bold(cyan("  Hermes Agent 交互式学习工具")))
    print(_hr("="))
    print(dim("  把 docs/getting-started-learning-guide.md 浓缩成分章课程 + 随堂测验。"))
    print(dim("  命令：数字选课 | h 帮助 | q 退出 | --list / --show N / --all / --reset"))
    print()


def _print_menu(data: dict) -> None:
    print()
    print(_hr("="))
    print(bold(cyan("主菜单")))
    print(_hr("="))
    total_lessons = len(LESSONS)
    done = sum(1 for l in LESSONS if _lesson_done(data, l.id))
    print(dim(f"进度：{done}/{total_lessons} 课完成"))
    print()
    for l in LESSONS:
        mark = green("✓") if _lesson_done(data, l.id) else "·"
        best = _best_score(data, l.id)
        score_str = ""
        if best is not None and l.questions:
            score_str = dim(f"  (最佳 {best}/{len(l.questions)})")
        print(f"  {mark} {bold(str(l.id))}. {l.title}{score_str}")
        print(f"       {dim(l.summary)}")
    print()
    print(dim("输入课程编号（或 m 菜单 / q 退出 / h 帮助）："))


def _menu_help() -> None:
    print()
    print(bold("帮助"))
    print(_hr("-"))
    print(dim("  数字     选择对应课程"))
    print(dim("  h        显示此帮助"))
    print(dim("  q        退出"))
    print()
    print(dim("  课程内命令："))
    print(dim("    Enter/n  下一页 / 进入测验"))
    print(dim("    p        上一页"))
    print(dim("    m        返回菜单"))
    print(dim("    r        重做本课测验"))
    print(dim("    q        退出"))
    print(_hr("-"))


# --------------------------------------------------------------------------- #
# 非交互模式
# --------------------------------------------------------------------------- #


def _print_lesson_noninteractive(lesson: Lesson) -> None:
    print()
    print(_hr("="))
    print(bold(f"课程 {lesson.id}：{lesson.title}"))
    print(dim(lesson.summary))
    print(_hr("="))
    for page in lesson.pages:
        print()
        print(_wrap(page))
    if lesson.questions:
        print()
        print(_hr("-"))
        print(bold("随堂测验"))
        print(_hr("-"))
        for qi, q in enumerate(lesson.questions, 1):
            print()
            print(cyan(f"Q{qi}: {q.prompt}"))
            for oi, opt in enumerate(q.options):
                tag = green("✓") if oi == q.answer else " "
                print(f"  [{tag}] {oi + 1}. {opt}")
            if q.explain:
                print(dim(f"  解释：{q.explain}"))
    if lesson.further_reading:
        print()
        print(dim("深入阅读："))
        for f in lesson.further_reading:
            print(dim(f"  - {f}"))


def _list_lessons() -> None:
    print(bold(cyan("Hermes Agent 交互式学习工具 —— 课程列表")))
    print()
    for l in LESSONS:
        print(f"  {bold(str(l.id))}. {l.title}  {dim('— ' + l.summary)}")
        if l.questions:
            print(dim(f"       ({len(l.questions)} 道测验题)"))
    print()
    print(dim(f"共 {len(LESSONS)} 课。用 --show N 查看第 N 课，--all 查看全部。"))


def _print_all() -> None:
    print(bold(cyan("Hermes Agent 交互式学习工具 —— 全部课程")))
    for lesson in LESSONS:
        _print_lesson_noninteractive(lesson)
    print()
    print(_hr("="))
    print(dim(f"共 {len(LESSONS)} 课。完整文档见 docs/getting-started-learning-guide.md"))


# --------------------------------------------------------------------------- #
# 主循环
# --------------------------------------------------------------------------- #


def _interactive(data: dict) -> None:
    _print_banner()
    while True:
        _print_menu(data)
        cmd = _prompt(dim("> "))
        if not cmd:
            continue
        if cmd.lower() in ("q", "quit", "exit"):
            print(dim("再见！继续学习用 docs/getting-started-learning-guide.md。"))
            _save_progress(data)
            return
        if cmd.lower() in ("h", "help", "?"):
            _menu_help()
            _ = _prompt(dim("按 Enter 返回..."))
            continue
        if cmd.lower() in ("l", "list"):
            _list_lessons()
            _ = _prompt(dim("按 Enter 返回..."))
            continue
        if cmd.isdigit():
            lid = int(cmd)
            lesson = next((l for l in LESSONS if l.id == lid), None)
            if lesson is None:
                print(red(f"没有课程 {lid}（范围 1-{len(LESSONS)}）"))
                continue
            _run_lesson(lesson, data)
            continue
        print(dim("未知命令。输入课程编号或 h 帮助或 q 退出。"))


def _parse_args() -> dict:
    args = sys.argv[1:]
    opts = {"list": False, "all": False, "show": None, "reset": False}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a == "--list":
            opts["list"] = True
        elif a == "--all":
            opts["all"] = True
        elif a == "--reset":
            opts["reset"] = True
        elif a == "--show":
            i += 1
            if i >= len(args):
                print(red("--show 需要一个课程编号"), file=sys.stderr)
                sys.exit(2)
            try:
                opts["show"] = int(args[i])
            except ValueError:
                print(red(f"--show 需要数字，得到 {args[i]!r}"), file=sys.stderr)
                sys.exit(2)
        else:
            print(red(f"未知参数 {a!r}，用 --help 查看用法"), file=sys.stderr)
            sys.exit(2)
        i += 1
    return opts


def main() -> None:
    opts = _parse_args()

    if opts["reset"]:
        try:
            PROGRESS_PATH.unlink()
            print(green(f"已清空进度：{PROGRESS_PATH}"))
        except FileNotFoundError:
            print(dim("没有进度文件可清。"))
        return

    if opts["list"]:
        _list_lessons()
        return

    if opts["all"]:
        _print_all()
        return

    if opts["show"] is not None:
        lesson = next((l for l in LESSONS if l.id == opts["show"]), None)
        if lesson is None:
            print(red(f"没有课程 {opts['show']}（范围 1-{len(LESSONS)}）"), file=sys.stderr)
            sys.exit(2)
        _print_lesson_noninteractive(lesson)
        return

    # 交互模式
    if not sys.stdin.isatty():
        # 无 TTY（管道/CI）：打印全部课程并退出，便于验证与脱机阅读
        print(dim("(检测到非交互环境，自动切换为打印全部课程)"))
        print()
        _print_all()
        return

    data = _load_progress()
    _interactive(data)


if __name__ == "__main__":
    main()
