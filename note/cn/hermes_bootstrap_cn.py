
"""Windows UTF-8 引导脚本（中文注释版）

Windows 下的 Python 有两个长期存在的文本编码陷阱：

1. ``sys.stdout`` / ``sys.stderr`` 绑定到控制台代码页（美国语言环境安装时为 cp1252），因此打印 "café" 会崩溃，并抛出 UnicodeEncodeError: 'charmap' 编解码器无法编码字符。

2. 通过 ``subprocess`` 生成的子进程不知道使用 UTF-8，除非在其环境中设置 ``PYTHONUTF8`` 和/或 ``PYTHONIOENCODING``——因此任何 Python 子进程（代码执行沙盒、代理子进程、语法检查子进程等）都会继承相同的 cp1252 默认值，并遇到相同的 UnicodeEncodeError。

本模块仅在 Windows 上修复这两个问题——POSIX 不受影响。必须在每个 Hermes 入口点的最开始导入（``hermes``、``hermes-agent``、``hermes-acp``、``python -m gateway.run``、``batch_runner.py``、``cron/scheduler.py``)，在任何其他可能进行文件 I/O 或打印到标准输出的导入之前。

Windows 上本模块的功能：

  * 设置 ``os.environ["PYTHONUTF8"] = "1"（PEP 540 UTF-8 模式），以便我们生成的每个子进程都对 ``open()`` 和标准输入/输出使用 UTF-8。
  * 设置 ``os.environ["PYTHONIOENCODING"] = "utf-8" 作为双保险——某些工具读取这个而不是 / 附加到 ``PYTHONUTF8``。
  * 使用 ``reconfigure()`` 方法（Python 3.7+）在当前进程中重新配置 ``sys.stdout`` / ``sys.stderr`` 为 UTF-8。这样可以在不重新执行的情况下修复父进程中的打印 "café" 问题。

本模块不做的事情：

  * 它不会使用 ``-X utf8`` 重新执行 Python，因此 *当前* 进程中的 ``open()`` 调用仍然默认使用区域设置编码。这些需要在调用位置显式指定 ``encoding="utf-8"``（lint 规则 ``PLW1514`` / ``PYI058``）。Ruff 是正确的工具来处理这种全面清理。

POSIX 上本模块的功能：

  * 什么也不做。POSIX 系统在 99% 的情况下默认使用 UTF-8，我们不想触及用户可能有意配置的 ``LANG`` / ``LC_*`` 行为。如果有人在 Linux 上遇到 C/POSIX 区域设置，他们可以自己导出 ``PYTHONUTF8=1``——我们不会覆盖它。

幂等性：可以安全多次调用。``_bootstrap_once`` 防止双重重新配置。
"""

from __future__ import annotations

import os
import sys

_IS_WINDOWS = sys.platform == "win32"
_bootstrap_applied = False


def 应用_Windows_UTF8_引导() -> bool:
    """如果我们在 Windows 上，则应用 Windows UTF-8 引导。

    返回 True 表示引导已应用（即我们在 Windows 上并且尚未执行此操作），否则 False。返回值仅供参考——调用者通常不需要它，但测试可能希望断言采用了该路径。

    幂等性：第一次调用之后的调用是无操作的。
    """
    global _bootstrap_applied

    if not _IS_WINDOWS:
        return False
    if _bootstrap_applied:
        return False

    # 1. 子进程继承这些并在 UTF-8 模式下运行。
    #    我们使用 setdefault() 而不是覆盖，以便用户可以通过在环境中设置 PYTHONUTF8=0 来显式选择退出（或 PYTHONIOENCODING=其他内容），如果他们真的想的话。
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # 2. 重新配置当前进程的标准输入/输出为 UTF-8。
    #    必要，因为 os.environ 更改不会追溯重新绑定 sys.stdout
    #    ——这些是在解释器启动时根据控制台代码页绑定的。
    #    ``reconfigure`` 是自 3.7 以来的 TextIOWrapper 方法。
    #
    #    errors="replace" 表示如果我们从标准输入读取非 UTF-8 内容（不太可能，但通过遗留工具的管道输入可能发生），我们将得到 U+FFFD 替换字符而不是崩溃。输出是纯 UTF-8。
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            # 不是 TextIOWrapper（测试中可能重定向到 BytesIO，或某些嵌入式情况下的非标准流）。
            # 静默跳过——环境变量修复对子进程仍然有效，这是更大的胜利。
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # 已关闭，或有人将其替换为不可重新配置的内容。非致命。
            pass

    # 标准输入也单独使用 errors="replace" 重新配置——来自遗留管道的输入不应使进程崩溃。
    stdin = getattr(sys, "stdin", None)
    if stdin is not None:
        reconfigure = getattr(stdin, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass

    _bootstrap_applied = True
    return True


# 在导入时应用——入口点只需在其模块的最开始需要 ``import hermes_bootstrap``（或 ``from hermes_bootstrap import 应用_Windows_UTF8_引导)，在导入任何其他内容之前。导入副作用会正确处理。
应用_Windows_UTF8_引导()

