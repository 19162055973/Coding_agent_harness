# PLAN · ForgeLoop 实现计划

> 每步可独立 subagent 完成；依赖已标注。验证均含「先写失败测试」。

**图例**：`[P]` 可并行 · `✓` 完成后填 commit hash

---

## Task 0 — 仓库骨架与工具链
- **目标**：pyproject、包结构、Makefile、gitignore、基础 CI 占位
- **文件**：`pyproject.toml`, `Makefile`, `.gitignore`, `src/forgeloop/__init__.py`, `.gitlab-ci.yml`
- **验证**：`pip install -e ".[dev]"`；`pytest` 可运行
- **状态**：✓ completed

## Task 1 — LLM 抽象 + MockLLM `[P]`
- **状态**：✓ completed

## Task 2 — WorkspaceGate + 文件工具 `[P]`
- **状态**：✓ completed

## Task 3 — 护栏策略
- **状态**：✓ completed

## Task 4 — Shell 工具 + 分发器
- **状态**：✓ completed

## Task 5 — 反馈传感器 + 失败分类（重点）
- **状态**：✓ completed

## Task 6 — 记忆存储 `[P]`
- **状态**：✓ completed

## Task 7 — 配置加载 `[P]`
- **状态**：✓ completed

## Task 8 — Agent 主循环
- **状态**：✓ completed

## Task 9 — 凭据存储
- **状态**：✓ completed

## Task 10 — 机制演示脚本
- **状态**：✓ completed

## Task 11 — FastAPI WebUI
- **状态**：✓ completed

## Task 12 — 分发与文档收尾
- **状态**：✓ completed

---

## 完成追踪

| Task | Status | Notes |
|------|--------|--------|
| 0–12 | completed | 同会话 TDD 交付；`pytest` 25 passed；机制演示通过 |

验证命令：`make test` · `make demo` · `make run`
