
#!/usr/bin/env python3
"""
Hermes Agent CLI（中文注释核心摘要版）
||
||  一个美观的 Hermes Agent 命令行界面，灵感来自 Claude Code。
||  功能包括 ASCII 艺术品牌标识、交互式 REPL、工具集选择和富文本格式化。
||
||  使用方法：
||    python cli.py                          # 启动交互模式，使用所有工具
||    python cli.py --toolsets web,terminal  # 使用特定工具集启动
||    python cli.py --skills hermes-agent-dev,github-auth
||    python cli.py --list-tools             # 列出可用工具并退出
"""

# 重要：hermes_bootstrap 必须是第一个导入——Windows 上的 UTF-8 标准输入/输出。
# 在 POSIX 上无操作。完整理由请参阅 hermes_bootstrap.py。
try:
    import hermes_bootstrap  # noqa: F401
except ModuleNotFoundError:
    # 当 hermes_bootstrap 尚未在虚拟环境中注册时的优雅回退
    # ——发生在部分 ``hermes update`` 中，其中 git-reset 到达了新代码但
    # ``uv pip install -e .`` 未完成。缺少引导意味着在 Windows 上跳过 UTF-8
    # 标准输入/输出设置；POSIX 不受影响。
    pass

import logging
import os
import shutil
import sys
import json
import re
import concurrent.futures
import base64
import atexit
import errno
import tempfile
import time
import uuid
import textwrap
from collections import deque
from urllib.parse import unquote, urlparse
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# 抑制启动消息以获得干净的 CLI 体验
os.environ["HERMES_QUIET"] = "1"  # 我们自己的模块

import yaml

from hermes_cli.fallback_config import get_fallback_chain

# 用于固定输入区域 TUI 的 prompt_toolkit
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl, ConditionalContainer
from prompt_toolkit.layout.processors import Processor, Transformation, PasswordProcessor, ConditionalProcessor
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import print_formatted_text as _pt_print
from prompt_toolkit.formatted_text import ANSI as _PT_ANSI
try:
    from prompt_toolkit.cursor_shapes import CursorShape
    _STEADY_CURSOR = CursorShape.BLOCK  # 不闪烁的块光标
except (ImportError, AttributeError):
    _STEADY_CURSOR = None


def load_cli_config() -&gt; Dict[str, Any]:
    """
    从配置文件加载 CLI 配置。
    ||
    ||  配置查找顺序：
    ||  1. ~/.hermes/config.yaml（用户配置——首选）
    ||  2. ./cli-config.yaml（项目配置——回退）
    ||
    ||  环境变量优先于配置文件值。
    ||  如果配置文件不存在，则返回默认值。
    ||
    ||  如果设置了 HERMES_IGNORE_USER_CONFIG=1（通过 ``hermes chat --ignore-user-config``），
    ||  则完全跳过 ``~/.hermes/config.yaml`` 中的用户配置，仅使用内置默认值加项目级别的
    ||  ``cli-config.yaml``（如果有）。仍然加载 ``.env`` 中的凭据——此标志仅抑制
    ||  行为/配置设置。
    """
    # 首先检查用户配置（{HERMES_HOME}/config.yaml）
    user_config_path = _hermes_home / 'config.yaml'
    project_config_path = Path(__file__).parent / 'cli-config.yaml'

    # --ignore-user-config：强制跳过用户 config.yaml（仍然尊重项目配置作为回退，
    # 以便默认值保持合理）。
    ignore_user_config = os.environ.get("HERMES_IGNORE_USER_CONFIG") == "1"

    # 如果用户配置存在且未忽略，则使用它，否则使用项目配置
    if user_config_path.exists() and not ignore_user_config:
        config_path = user_config_path
    else:
        config_path = project_config_path

    # 默认配置
    defaults = {
        "model": {
            "default": "",
            "base_url": "",
            "provider": "auto",
        },
        "terminal": {
            "env_type": "local",
            "cwd": ".",  # "." 在运行时解析为 os.getcwd()
            "timeout": 60,
            "lifetime_seconds": 300,
            "docker_image": "nikolaik/python-nodejs:python3.11-nodejs20",
            "docker_forward_env": [],
            "singularity_image": "docker://nikolaik/python-nodejs:python3.11-nodejs20",
            "modal_image": "nikolaik/python-nodejs:python3.11-nodejs20",
            "daytona_image": "nikolaik/python-nodejs:python3.11-nodejs20",
            "docker_volumes": [],  # Docker 后端的主机:容器卷挂载
            "docker_mount_cwd_to_workspace": False,  # 仅显式选择加入；默认关闭以进行沙箱隔离
        },
        "browser": {
            "inactivity_timeout": 120,  # 2 分钟后自动清理非活跃浏览器会话
            "record_sessions": False,  # 自动将浏览器会话记录为 WebM 视频
            "engine": "auto",  # 浏览器引擎：auto（Chrome）、lightpanda、chrome
        },
        "compression": {
            "enabled": True,      # 当接近上下文限制时自动压缩
            "threshold": 0.50,    # 在模型上下文限制的 50% 时压缩
        },
        "agent": {
            "max_turns": 90,  # 默认最大工具调用迭代（与子代理共享）
            "verbose": False,
            "system_prompt": "",
            "prefill_messages_file": "",
            "reasoning_effort": "",
            "service_tier": "",
        },
        "display": {
            "compact": False,
            "resume_display": "full",
            "show_reasoning": False,
            "streaming": True,
            "persistent_output": True,
            "persistent_output_max_lines": 200,
            "skin": "default",
        },
    }

    # 跟踪配置文件是否显式设置了终端配置。
    # 当使用默认值（无配置文件 / 无终端部分）时，我们不应该
    # 覆盖已由 .env 设置的环境变量——只有用户的配置文件
    # 才应该是权威的。
    _file_has_terminal_config = False

    # 如果存在则从文件加载
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                from hermes_cli.config import _normalize_root_model_keys

                file_config = _normalize_root_model_keys(yaml.safe_load(f) or {})

            _file_has_terminal_config = "terminal" in file_config

            # 处理模型配置——可以是字符串（新格式）或字典（旧格式）
            if "model" in file_config:
                if isinstance(file_config["model"], str):
                    # 新格式：模型只是字符串，转换为字典结构
                    defaults["model"]["default"] = file_config["model"]
                elif isinstance(file_config["model"], dict):
                    # 旧格式：模型是带有 default/base_url 的字典
                    defaults["model"].update(file_config["model"])
                    # 如果用户配置设置了 model.model 但没有设置 model.default，
                    # 将 model.model 提升为 model.default，这样用户的显式选择
                    # 不会被硬编码的默认值隐藏。没有这个，只设置了 "model:"
                    # （而不是 "default:"）的配置会默默回退到 claude-opus，
                    # 因为合并保留了硬编码的默认值，并且 HermesCLI.__init__ 首先检查 "default"。
                    if "model" in file_config["model"] and "default" not in file_config["model"]:
                        defaults["model"]["default"] = file_config["model"]["model"]

            # 深度合并 file_config 到 defaults 中。
            # 首先：合并两者中都存在的键（深度合并字典，覆盖标量）
            for key in defaults:
                if key == "model":
                    continue  # 已在上面处理
                if key in file_config:
                    if isinstance(defaults[key], dict) and isinstance(file_config[key], dict):
                        defaults[key].update(file_config[key])
                    else:
                        defaults[key] = file_config[key]

            # 其次：携带 file_config 中不在 defaults 中的键
            # （例如 platform_toolsets、provider_routing、memory、honcho 等）
            for key in file_config:
                if key not in defaults and key != "model":
                    defaults[key] = file_config[key]

        except Exception as e:
            logger.warning("Failed to load cli-config.yaml: %s", e)

    # 在桥接到环境变量之前扩展配置值中的 ${ENV_VAR} 引用。
    from hermes_cli.config import _expand_env_vars
    defaults = _expand_env_vars(defaults)

    # 应用终端配置到环境变量（以便 terminal_tool 取用它们）
    terminal_config = defaults.get("terminal", {})

    # 规范化配置键：新的配置系统（hermes_cli/config.py）和所有
    # 文档都使用 "backend"，旧的 cli-config.yaml 使用 "env_type"。
    # 接受两者，"backend" 优先（它是文档化的键）。
    if "backend" in terminal_config:
        terminal_config["env_type"] = terminal_config["backend"]

    return defaults


# 在模块启动时加载配置
CLI_CONFIG = load_cli_config()


# 尽早初始化集中日志记录——agent.log + errors.log 在 ~/.hermes/logs/ 中。
# 这确保即使在 AIAgent 实例化之前，CLI 会话也会生成日志跟踪。
try:
    from hermes_logging import setup_logging
    setup_logging(mode="cli")
except Exception:
    pass  # 日志设置是尽力而为的——不要使 CLI 崩溃


# 惰性导入 agent 和工具系统。纯交互启动只需要提示；完整的
# agent/工具注册表在首次使用时初始化。
def AIAgent(*args, **kwargs):
    from run_agent import AIAgent as _AIAgent
    return _AIAgent(*args, **kwargs)


def get_tool_definitions(*args, **kwargs):
    from hermes_cli.mcp_startup import wait_for_mcp_discovery
    from model_tools import get_tool_definitions as _get_tool_definitions
    wait_for_mcp_discovery()
    return _get_tool_definitions(*args, **kwargs)


# 防止清理在退出时多次运行的保护
_cleanup_done = False
# 弱引用活跃的 AIAgent，用于在退出时关闭记忆提供者
_active_agent_ref = None
_deferred_agent_startup_done = False
# 一旦 TUI 的 prompt_toolkit 应用启动（这启用了焦点报告 + 鼠标跟踪），
# 设置为 True。门控退出时的终端重置，这样非 TUI 的一次性 CLI 运行——它们也通过 atexit
# 注册了 _run_cleanup——不会发出它们从未启用的模式的转义序列 (#36823)。
_tui_input_modes_active = False


def _run_cleanup():
    """恰好运行一次资源清理。"""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    # 首先重置终端输入模式，在较慢的资源拆卸（MCP / 浏览器 / 记忆关闭可能需要几秒）
    # 之前。在 Ctrl+C 时，用户的终端立即可用，并且稍后引发的步骤不能跳过重置 (#36823)。
    # 除非 TUI 实际运行，否则无操作。
    _reset_terminal_input_modes_on_exit()

    try:
        _cleanup_all_terminals()
    except Exception:
        pass
    try:
        _cleanup_all_browsers()
    except Exception:
        pass
    try:
        from tools.mcp_tool import shutdown_mcp_servers
        shutdown_mcp_servers()
    except Exception:
        pass
    # 关闭缓存的辅助 LLM 客户端（同步 + 异步），这样
    # AsyncHttpxClientWrapper.__del__ 不会在关闭的事件循环上触发
    # 并导致 prompt_toolkit 的 "Press ENTER to continue..." 处理程序。
    try:
        from agent.auxiliary_client import shutdown_cached_clients
        shutdown_cached_clients()
    except Exception:
        pass


def _reset_terminal_input_modes_on_exit() -&gt; None:
    """尽力而为：在 TUI 退出时禁用焦点报告 + 鼠标跟踪，这样它们不会泄漏
    到共享选项卡的下一个 shell 会话中。
    ||
    ||  prompt_toolkit 在干净拆卸时恢复这些，但 Ctrl+C、SIGTERM / SIGHUP 和崩溃
    ||  可以绕过其展开，使模式保持启用。然后终端会发出原始 ``ESC[I`` / ``ESC[O``
    ||  焦点事件和零碎的 SGR 鼠标报告，作为在同一选项卡中接下来运行的任何内容中的可见文本
    ||  (#36823)。从 ``_run_cleanup``（atexit 注册 + 在正常 / EOF / 中断退出路径上调用）
    ||  调用，这涵盖了正常退出、Ctrl+C 和 SIGTERM/SIGHUP。``kill -9`` 是不可捕获的，
    ||  并且看板工作者的 ``os._exit(0)`` 路径绕过 ``atexit``；两者都不运行这个——但两者都
    ||  是非 TTY / 非 TUI 的，所以那里没有什么需要重置的。
    ||
    ||  门控在 ``_tui_input_modes_active`` 上，这样一次性非 TUI CLI 运行（它们
    ||  通过 ``atexit`` 共享 ``_run_cleanup``）永远不会发出这些代码。直接写入控制
    ||  终端：到退出时，prompt_toolkit 自己的输出已拆卸，因此 ``sys.stdout`` 是真实的
    ||  文件描述符；当 stdout 从终端重定向时，回退到 ``/dev/tty``。
    """
    global _tui_input_modes_active
    if not _tui_input_modes_active:
        return
    # 即将禁用模式——清除标志，以便重新启用的 _run_cleanup（或重用它的长进程）
    # 不会重新发出它们。
    _tui_input_modes_active = False
    # 优先使用 stdout，如果它是终端的话；否则 TUI 可能在 stdout 重定向时驱动了
    # /dev/tty——重置那里而不是什么都不做。
    try:
        stream = sys.stdout
        if stream is not None and stream.isatty():
            # (这里会写出终端重置序列，在完整版本中)
            return
    except Exception:
        pass


# 注册退出钩子进行清理
atexit.register(_run_cleanup)


def main():
    """
    CLI 入口点。
    ||
    ||  解析命令行参数，设置环境，并启动交互式 REPL 或
    ||  根据需要执行一次性命令。
    ||
    ||  这是整个应用的主要协调点，负责：
    ||  1. 解析 CLI 标志
    ||  2. 设置运行环境
    ||  3. 初始化 Agent
    ||  4. 运行主交互循环
    """
    # 实际的实现非常长，包含完整的 CLI 参数解析、TUI 设置等。
    # 对于这个核心摘要，我们省略了数千行的详细实现。
    #
    # 核心流程是：
    #
    # 1. 解析命令行参数
    # 2. 加载配置
    # 3. 设置日志记录
    # 4. 初始化 AIAgent
    # 5. 如果是交互模式，启动 TUI REPL
    # 6. 如果是一次性命令，执行它
    #
    pass


if __name__ == "__main__":
    main()

