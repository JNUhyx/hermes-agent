
"""Agent 对话循环（中文注释核心摘要版）
||
||  这是从 ``run_agent.AIAgent`` 中提取的最大单一块代码。
||  大约 3,900 行的 ``run_conversation`` 函数体，驱动代理完成一次用户对话轮次
||  （模型调用、工具分发、重试、回退、压缩、轮次后钩子、后台记忆/技能审查提示）。
||
||  该函数将父 ``AIAgent`` 实例作为第一个参数（``agent``），并通过属性查找访问其状态。
||  ``_ra().AIAgent.run_conversation`` 现在是一个薄的转发器。
||
||  生产代码或测试直接在 ``run_agent`` 上修补的符号（``handle_function_call``、
||  ``_set_interrupt``、``OpenAI`` 等）通过 ``_ra()`` 解析，以便这些修补继续生效。
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import ssl
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _ra():
    """延迟引用 ``run_agent`` 模块。
    ||
    ||  这样调用者可以修补 ``run_agent.handle_function_call`` / ``run_agent._set_interrupt`` /
    ||  ``run_agent.OpenAI``，并且这些修补能到达这个代码路径。
    """
    import run_agent
    return run_agent


def run_conversation(
    agent,
    user_message: str,
    system_message: str = None,
    conversation_history: List[Dict[str, Any]] = None,
    task_id: str = None,
    stream_callback: Optional[callable] = None,
    persist_user_message: Optional[str] = None,
) -&gt; Dict[str, Any]:
    """运行完整的对话，包含工具调用，直到完成。
    ||
    ||  参数：
    ||    user_message (str)：用户的消息/问题
    ||    system_message (str)：自定义系统提示（可选，如果提供则覆盖 ephemeral_system_prompt）
    ||    conversation_history (List[Dict])：先前的对话历史（可选）
    ||    task_id (str)：此任务的唯一标识符，用于在并发任务之间隔离 VM（可选，如果未提供则自动生成）
    ||    stream_callback：可选回调，在流式传输期间随每个文本增量调用。
    ||      TTS 管道使用它在完整响应之前开始音频生成。
    ||      当为 None（默认）时，API 调用使用标准的非流式路径。
    ||    persist_user_message：可选的干净用户消息，用于在转录/历史记录中存储，
    ||      当 user_message 包含仅用于 API 的合成前缀时。
    ||
    ||  返回：
    ||    Dict：完整的对话结果，包含最终响应和消息历史
    """
    # 保护标准输入/输出免受管道破损导致的 OSError（systemd/无头进程/守护进程）。
    # 只安装一次，在流健康时是透明的，防止写入时崩溃。
    _install_safe_stdio()

    agent._ensure_db_session()

    # 告诉 auxiliary_client 当前轮次的活跃主提供商/模型是什么。
    # 由行为依赖于活跃主模型的工具使用（例如 vision_analyze 的原生快速路径），
    # 这样它们看到 CLI/网关覆盖而不是过时的 config.yaml 默认值。
    # 幂等性——每轮调用都没问题。
    try:
        from agent.auxiliary_client import set_runtime_main
        set_runtime_main(
            getattr(agent, "provider", "") or "",
            getattr(agent, "model", "") or "",
            base_url=getattr(agent, "base_url", "") or "",
            api_key=getattr(agent, "api_key", "") or "",
            api_mode=getattr(agent, "api_mode", "") or "",
        )
    except Exception:
        pass

    # 在该线程上标记所有日志记录，附加会话 ID，这样 ``hermes logs --session &lt;id&gt;``
    # 可以过滤单个对话。
    set_session_context(agent.session_id)

    # 为此线程绑定技能写入源 ContextVar，以便工具处理程序（例如 skill_manage create）
    # 可以判断它们是在后台代理改进审查分支中运行，还是在前台用户导向轮次中运行。
    # 在每次调用的顶部设置；审查分支在自己的线程上运行，有新鲜上下文，
    # 因此这里的前台值不会泄漏到那里。
    set_current_write_origin(getattr(agent, "_memory_write_origin", "assistant_tool"))

    # 如果前一轮激活了回退，则恢复主运行时，以便本轮获得首选模型的新鲜尝试。
    # 当 _fallback_activated 为 False 时无操作（网关、第一轮等）。
    agent._restore_primary_runtime()

    # 从用户输入中清理代理对字符。从富文本编辑器（Google Docs、Word 等）剪贴板粘贴
    # 可能会注入单独的代理对，这些在 UTF-8 中无效，会在 OpenAI SDK 中使 json.dumps 崩溃。
    if isinstance(user_message, str):
        user_message = _sanitize_surrogates(user_message)
    if isinstance(persist_user_message, str):
        persist_user_message = _sanitize_surrogates(persist_user_message)

    # 存储流回调，供 _interruptible_api_call 取用
    agent._stream_callback = stream_callback
    agent._persist_user_message_idx = None
    agent._persist_user_message_override = persist_user_message
    # 如果未提供，则生成唯一的 task_id 以在并发任务之间隔离 VM
    effective_task_id = task_id or str(uuid.uuid4())
    # 暴露活跃的 task_id，以便在轮次中运行的工具（例如 delegate_tool.py 中的 delegate_task）
    # 可以识别此代理以用于跨代理文件状态注册表。在任何工具分发之前设置，
    # 以便在子进程启动时拍摄的快照看到父进程的真实 ID，而不是 None。
    agent._current_task_id = effective_task_id

    # 在每轮开始时重置重试计数器和迭代预算，以便上一轮的子代理使用
    # 不会消耗下一轮的预算。
    agent._invalid_tool_retries = 0
    agent._invalid_json_retries = 0
    agent._empty_content_retries = 0
    agent._incomplete_scratchpad_retries = 0
    agent._codex_incomplete_retries = 0
    agent._thinking_prefill_retries = 0
    agent._post_tool_empty_retried = False
    agent._last_content_with_tools = None
    agent._last_content_tools_all_housekeeping = False
    agent._mute_post_response = False
    agent._unicode_sanitization_passes = 0
    agent._tool_guardrails.reset_for_turn()
    agent._tool_guardrail_halt_decision = None
    # 在服务器拒绝带有错误的 image_url 内容部分（例如 "Only 'text' content type is supported."）
    # 之前保持为 True。在第一次拒绝后设置为 False，并在会话的其余部分保持 False，
    # 这样我们就不会重新发送图像到纯文本端点。
    # 作用域为每个 ``_run()`` 调用，而不是每个实例。
    agent._vision_supported = True

    # 轮次前连接健康检查：检测和清理提供商故障或断开的流留下的死 TCP 连接。
    # 这防止下一次 API 调用挂在僵尸套接字上。
    if agent.api_mode != "anthropic_messages":
        try:
            if agent._cleanup_dead_connections():
                agent._emit_status(
                    "🔌 检测到来自先前提供商问题的陈旧连接——已自动清理。正在使用新鲜连接继续。"
                )
        except Exception:
            pass
    # 通过 status_callback 为网关平台重放压缩警告
    # （回调在 __init__ 期间未连接）。
    if agent._compression_warning:
        agent._replay_compression_warning()
        agent._compression_warning = None  # 仅发送一次

    # 注意：_turns_since_memory 和 _iters_since_skill 未在此重置。
    # 它们在 __init__ 中初始化，并且必须在 run_conversation 调用之间持久化，
    # 以便提示逻辑在 CLI 模式下正确累积。
    agent.iteration_budget = IterationBudget(agent.max_iterations)

    # 记录对话轮次开始，用于调试/可观察性
    _preview_text = _summarize_user_message_for_log(user_message)
    _msg_preview = (_preview_text[:80] + "...") if len(_preview_text) &gt; 80 else _preview_text
    _msg_preview = _msg_preview.replace("\n", " ")
    logger.info(
        "conversation turn: session=%s model=%s provider=%s platform=%s history=%d msg=%r",
        agent.session_id or "none", agent.model, agent.provider or "unknown",
        agent.platform or "unknown", len(conversation_history or []),
        _msg_preview,
    )

    # 初始化对话（复制以避免改变调用者的列表）
    messages = list(conversation_history) if conversation_history else []

    # 从对话历史中恢复待办事项存储（网关为每个消息创建一个新鲜的 AIAgent，
    # 因此内存存储为空——我们需要从历史记录中最近的待办事项工具响应中恢复待办事项状态）
    if conversation_history and not agent._todo_store.has_items():
        agent._hydrate_todo_store(conversation_history)

    # 从持久化历史中恢复每轮次的提示计数器。
    # 网关为每个入站消息创建一个新鲜的 AIAgent（缓存未命中 / 1 小时空闲驱逐 /
    # 配置签名不匹配 / 进程重启），因此 _turns_since_memory 和 _user_turn_count
    # 每轮都从 0 开始，并且 memory.nudge_interval 触发可能永远不会到达。
    # 从 conversation_history 中的先前用户轮次重建有效计数。
    # 幂等性：已累积计数器的缓存代理保留它们；仅具有空内存状态的新鲜构建代理会恢复。
    if conversation_history and agent._user_turn_count == 0:
        prior_user_turns = sum(
            1 for m in conversation_history if m.get("role") == "user"
        )
        if prior_user_turns &gt; 0:
            agent._user_turn_count = prior_user_turns
            if agent._memory_nudge_interval &gt; 0 and agent._turns_since_memory == 0:
                # % 保留原始的 N 分之一节奏，而不是在恢复时立即触发审查
                # （这会让会话恰好落在 N 的倍数之后的用户感到惊讶）。
                agent._turns_since_memory = prior_user_turns % agent._memory_nudge_interval


    # 预填充消息（少样本引导）仅在 API 调用时注入，永远不会存储在 messages 列表中。
    # 这使它们保持临时性：它们不会保存到会话数据库、会话日志或批量轨迹中，
    # 但它们会在每次 API 调用时自动重新应用（包括会话继续）。

    # 跟踪用户轮次，用于记忆刷新和定期提示逻辑
    agent._user_turn_count += 1

    # 在每轮开始时重置流式传输上下文清理器，以便先前被中断流的挂起跨度
    # 不会污染本轮输出。
    scrubber = getattr(agent, "_stream_context_scrubber", None)
    if scrubber is not None:
        scrubber.reset()
    # 为相同原因重置思考清理器——先前被中断的流可能让我们处于未终止的块中。
    think_scrubber = getattr(agent, "_stream_think_scrubber", None)
    if think_scrubber is not None:
        think_scrubber.reset()

    # 保留原始用户消息（没有提示注入）。
    original_user_message = persist_user_message if persist_user_message is not None else user_message

    # 跟踪记忆提示触发（基于轮次，在此检查）。
    # 技能提示在代理循环完成后检查，基于本轮使用了多少工具迭代。
    _should_review_memory = False
    if (agent._memory_nudge_interval &gt; 0
            and "memory" in agent.valid_tool_names
            and agent._memory_store):
        agent._turns_since_memory += 1
        if agent._turns_since_memory &gt;= agent._memory_nudge_interval:
            _should_review_memory = True
            agent._turns_since_memory = 0

    # 添加用户消息
    user_msg = {"role": "user", "content": user_message}
    messages.append(user_msg)
    current_turn_user_idx = len(messages) - 1
    agent._persist_user_message_idx = current_turn_user_idx

    if not agent.quiet_mode:
        _print_preview = _summarize_user_message_for_log(user_message)
        agent._safe_print(f"💬 开始对话：'{_print_preview[:60]}{'...' if len(_print_preview) &gt; 60 else ''}'")

    # ── 系统提示（为前缀缓存按会话缓存）────────────────
    # 第一次调用时构建一次，对所有后续调用重用。
    # 仅在上下文压缩事件后重建（这会使缓存无效并从磁盘重新加载记忆）。
    #
    # 对于继续的会话（网关为每个消息创建一个新鲜的 AIAgent），我们从会话数据库
    # 加载存储的系统提示，而不是重建。重建会从磁盘提取模型已经知道的记忆更改
    # （它写入的！），产生不同的系统提示并破坏 Anthropic 前缀缓存。
    if agent._cached_system_prompt is None:
        _restore_or_build_system_prompt(agent, system_message, conversation_history)

    active_system_prompt = agent._cached_system_prompt

    # 主对话循环
    api_call_count = 0
    final_response = None
    interrupted = False
    failed = False
    codex_ack_continuations = 0
    length_continue_retries = 0
    truncated_tool_call_retries = 0
    truncated_response_parts: List[str] = []
    compression_attempts = 0
    _turn_exit_reason = "unknown"  # 诊断：循环为何退出

    # 每轮文件变更验证器状态。按解析的路径键入；
    # 每个失败的 ``write_file`` / ``patch`` 调用记录错误预览。
    # 稍后对同一路径的成功写入会移除该条目（模型已恢复）。
    # 在轮次结束时，仍存在的任何条目会在建议性页脚中显示，
    # 这样模型就不能过度声称成功，而文件在磁盘上实际上未更改。
    agent._turn_failed_file_mutations: Dict[str, Dict[str, Any]] = {}

    # 记录执行线程，以便 interrupt()/clear_interrupt() 可以
    # 将工具级中断信号的作用域限制为 *仅* 此代理的线程。
    # 必须在任何线程作用域的中断同步之前设置。
    agent._execution_thread_id = threading.current_thread().ident

    # 始终清除前一轮留下的陈旧的每线程状态。如果在启动完成前到达中断，
    # 保留它并将其绑定到此执行线程，而不是丢弃它。
    _ra()._set_interrupt(False, agent._execution_thread_id)
    if agent._interrupt_requested:
        _ra()._set_interrupt(True, agent._execution_thread_id)
        agent._interrupt_thread_signal_pending = False
    else:
        agent._interrupt_message = None
        agent._interrupt_thread_signal_pending = False

    # 通知记忆提供者新轮次开始，以便节奏跟踪工作。
    # 必须在 prefetch_all() 之前发生，以便提供者知道是哪一轮，
    # 并且可以通过 contextCadence/dialecticCadence 限制上下文/辩证刷新。
    if agent._memory_manager:
        try:
            _turn_msg = original_user_message if isinstance(original_user_message, str) else ""
            agent._memory_manager.on_turn_start(agent._user_turn_count, _turn_msg)
        except Exception:
            pass

    # 外部记忆提供者：在工具循环之前预取一次。
    # 在每次迭代中重用缓存结果，以避免在每次工具调用时重新调用 prefetch_all()
    # （10 次工具调用 = 10 倍延迟 + 成本）。
    # 使用 original_user_message（干净输入）——user_message 可能包含
    # 注入的技能内容，这会膨胀/破坏提供者查询。
    _ext_prefetch_cache = ""
    if agent._memory_manager:
        try:
            _query = original_user_message if isinstance(original_user_message, str) else ""
            _ext_prefetch_cache = agent._memory_manager.prefetch_all(_query) or ""
        except Exception:
            pass

    # 可选的启用运行时：如果 api_mode == codex_app_server，将轮次交给
    # codex 应用服务器子进程（终端/文件操作/修补都在 Codex 中运行）。
    # 完全绕过默认的 Hermes 路径。
    # 有关适配器，请参阅 agent/transports/codex_app_server_session.py；
    # 有关理由，请参阅 references/codex-app-server-runtime.md。
    if agent.api_mode == "codex_app_server":
        return agent._run_codex_app_server_turn(
            user_message=user_message,
            original_user_message=original_user_message,
            messages=messages,
            effective_task_id=effective_task_id,
            should_review_memory=_should_review_memory,
        )

    # ========== 主循环开始 ==========
    # 实际的 "思考 → 行动 → 反馈" 循环在这里发生
    # 为了保持此摘要文件简洁，我们省略了数千行的详细循环实现
    # 核心流程是：
    #
    # 1. 准备 API 消息（系统提示 + 对话历史）
    # 2. 调用 LLM API（可能流式传输）
    # 3. 解析响应，提取工具调用
    # 4. 执行工具调用
    # 5. 将工具结果添加回对话历史
    # 6. 重复直到获得最终答案或达到迭代限制
    #
    # ========== 主循环结束 ==========

    # 返回完整的对话结果
    return {
        "messages": messages,
        "final_response": final_response,
        "interrupted": interrupted,
        "failed": failed,
    }


def _restore_or_build_system_prompt(agent, system_message, conversation_history):
    """从会话数据库恢复缓存的系统提示，或从头构建。
    ||
    ||  改变 ``agent._cached_system_prompt`` 并在第一次构建时将新构建的提示持久化回会话数据库。
    ||  从 ``run_conversation`` 中提取，以便前缀缓存恢复路径可以被孤立测试。
    ||
    ||  存储行的三态区分，通过日志暴露，以便静默前缀缓存未命中在 ``agent.log`` 中可见：
    ||
    ||    * ``missing``——尚无会话行（合法的第一轮）。
    ||    * ``null``——行存在，``system_prompt`` 列为 NULL。
    ||      遗留会话，早于系统提示持久化，或迁移遗留物。当 ``conversation_history`` 非空时发出警告。
    ||    * ``empty``——行存在，``system_prompt`` 列为空字符串。
    ||      表示前一轮次写入已运行但未存储任何内容（静默持久化错误）。始终警告。
    ||    * ``present``——行存在并带有可用提示——完全重用。
    ||
    ||  读取或写入会话数据库失败时记录 WARNING（不是 DEBUG），以便持久化问题（磁盘满、
    ||  架构漂移、锁争用）浮出水面，而不需要详细模式。这以前是一个调试级别的日志，
    ||  静默破坏了网关路径上的前缀缓存重用（该路径为每个轮次构建新鲜的 AIAgent 并依赖于此数据库往返）。
    """
    stored_prompt = None
    stored_state = "missing"
    if conversation_history and agent._session_db:
        try:
            session_row = agent._session_db.get_session(agent.session_id)
            if session_row is not None:
                raw_prompt = session_row.get("system_prompt")
                if raw_prompt is None:
                    stored_state = "null"
                elif raw_prompt == "":
                    stored_state = "empty"
                else:
                    stored_prompt = raw_prompt
                    stored_state = "present"
        except Exception as exc:
            logger.warning(
                "Session DB get_session failed for system-prompt restore "
                "(session=%s): %s. Falling back to fresh build — prefix "
                "cache will miss for this turn.",
                agent.session_id, exc,
            )

    if stored_prompt:
        # 继续会话——完全重用前一轮的系统提示，以便 Anthropic 缓存前缀匹配。
        agent._cached_system_prompt = stored_prompt
        return

    if conversation_history and stored_state in ("null", "empty"):
        # 继续的会话，其存储的提示不可用。前一轮的写入要么从未发生，
        # 要么写入了空字符串——无论哪种方式，每轮现在都重建，并且前缀缓存每次都未命中。
        logger.warning(
            "Stored system prompt for session %s is %s; rebuilding "
            "from scratch this turn. Prefix cache will miss until "
            "the rebuild persists. Investigate the previous turn's "
            "update_system_prompt write path.",
            agent.session_id, stored_state,
        )

    # 新会话的第一轮（或从破坏的存储提示恢复）——从头构建。
    agent._cached_system_prompt = agent._build_system_prompt(system_message)

    # 插件钩子：on_session_start——当创建全新会话时触发一次（而不是在继续时）。
    # 插件可以使用它来初始化会话作用域状态（例如预热记忆缓存）。
    try:
        from hermes_cli.plugins import invoke_hook as _invoke_hook
        _invoke_hook(
            "on_session_start",
            session_id=agent.session_id,
            model=agent.model,
            platform=getattr(agent, "platform", None) or "",
        )
    except Exception as exc:
        logger.warning("on_session_start hook failed: %s", exc)

    # 在 SQLite 中持久化系统提示快照。这里的失败以前记录在 DEBUG 级别，
    # 这在网关路径上静默破坏了前缀缓存重用（每个轮次新鲜 AIAgent → 从该行读取
    # 以用于每个后续轮次）。
    if agent._session_db:
        try:
            agent._session_db.update_system_prompt(agent.session_id, agent._cached_system_prompt)
        except Exception as exc:
            logger.warning(
                "Session DB update_system_prompt failed for session %s: "
                "%s. Subsequent turns will rebuild the system prompt and "
                "miss the prefix cache.",
                agent.session_id, exc,
            )

