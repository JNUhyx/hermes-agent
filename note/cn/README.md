
# Hermes 中文学习文件索引

欢迎使用 Hermes 中文学习资源！这里包含了 Hermes 项目核心文件的中文注释版本。

---

## 📁 目录结构

```
/workspace/note/
├── hermes-study-plan.md          # 学习计划（先前创建）
└── cn/
    ├── README.md                  # 本文件
    ├── hermes_bootstrap_cn.py     # Windows UTF-8 引导脚本
    ├── conversation_loop_cn.py    # Agent 对话循环（核心摘要）
    └── cli_cn.py                  # CLI 入口（核心摘要）
```

---

## 📚 学习文件说明

### 1. [hermes_bootstrap_cn.py](file:///workspace/note/cn/hermes_bootstrap_cn.py)
**功能**：Windows 系统下的 UTF-8 编码引导脚本

**学习重点**：
- 解决 Windows 下 Python 的 Unicode 编码问题
- 理解环境变量配置（`PYTHONUTF8`、`PYTHONIOENCODING`）
- 学习如何在模块导入时自动执行初始化

---

### 2. [conversation_loop_cn.py](file:///workspace/note/cn/conversation_loop_cn.py)
**功能**：Agent 的核心对话循环（核心摘要版）

**学习重点**：
- 理解 "思考 → 行动 → 反馈" 的完整循环流程
- 学习会话管理和系统提示缓存机制
- 理解工具调用的编排和重试逻辑
- 上下文压缩策略和记忆管理

**关键函数**：
- `run_conversation()` - 主对话循环入口
- `_restore_or_build_system_prompt()` - 系统提示恢复/构建

---

### 3. [cli_cn.py](file:///workspace/note/cn/cli_cn.py)
**功能**：Hermes 命令行界面（核心摘要版）

**学习重点**：
- CLI 参数解析和配置加载
- TUI（终端用户界面）初始化
- 资源清理和退出钩子

**关键函数**：
- `load_cli_config()` - 配置加载
- `_run_cleanup()` - 资源清理
- `main()` - 主入口点

---

## 🎯 学习路径建议

### 初学者路径（第 1-2 周）
1. **先读** `hermes_bootstrap_cn.py` - 理解项目启动
2. **再读** `cli_cn.py` - 理解用户交互入口
3. **最后读** `conversation_loop_cn.py` - 理解 Agent 核心逻辑

### 进阶路径（第 3-4 周）
1. 阅读原始完整文件（不在 `/workspace/note/cn/` 中）
2. 动手尝试修改和运行代码
3. 阅读测试用例，理解预期行为
4. 尝试编写简单插件或工具

---

## ⚠️ 重要说明

1. **所有 `_cn.py` 文件都保留原始代码**，仅添加中文注释
2. **文件可以正常运行**，不会破坏功能
3. **注释格式**：使用 `# || ...` 表示中文注释，便于区分
4. **摘要版与完整版**：`conversation_loop_cn.py` 和 `cli_cn.py` 是核心摘要，
   完整版文件位于项目根目录。

---

## 📖 进一步学习

- 返回 [hermes-study-plan.md](file:///workspace/note/hermes-study-plan.md) 查看完整学习计划
- 阅读项目根目录的 [README.md](file:///workspace/README.md) 和 [README.zh-CN.md](file:///workspace/README.zh-CN.md)
- 探索 `/workspace/agent/`、`/workspace/tools/`、`/workspace/gateway/` 等目录

---

## 🚀 快速开始

验证文件是否可以正常运行：

```bash
cd /workspace/note/cn
python -c "import sys; sys.path.insert(0, '.'); import hermes_bootstrap_cn; print('✓ hermes_bootstrap_cn.py 正常')"
```

---

祝你学习愉快！🎉

