# PLAN · ForgeLoop 实现计划

> 每步可独立 subagent 完成；依赖已标注。验证均含「先写失败测试」。
> 2026-08-12 冷启动后恢复 Task 1–2 完整卡片（见 `SPEC_PROCESS.md` / `cold_start_scratch/REPORT.md`）。

**图例**：`[P]` 可并行 · `✓` 完成后填 commit hash

---

## Task 0 — 仓库骨架与工具链
- **目标**：pyproject、包结构、Makefile、gitignore、基础 CI 占位
- **文件**：`pyproject.toml`, `Makefile`, `.gitignore`, `src/forgeloop/__init__.py`, `.gitlab-ci.yml`
- **验证**：`pip install -e ".[dev]"`；`pytest` 可运行
- **状态**：✓ completed · `21e7ab1`

## Task 1 — LLM 抽象 + MockLLM `[P]`
- **目标**：定义 `LLMPort` / `LLMMessage` / `LLMResponse` / `LLMError`；实现按脚本队列吐出预定动作的 `MockLLM`；单测不触网
- **文件**：`src/forgeloop/llm/base.py`, `src/forgeloop/llm/mock.py`, `src/forgeloop/models.py`, `tests/test_llm_mock.py`
- **验证**：
  - 先写失败测试：队列按序返回预定 `AgentAction`；队列耗尽抛 `LLMError`；不发起 HTTP
  - `pytest tests/test_llm_mock.py` 通过
- **依赖**：Task 0
- **状态**：✓ completed · `f486eba`

## Task 2 — WorkspaceGate + 文件工具 `[P]`
- **目标**：`WorkspaceGate` 解析相对路径并拒绝逃逸；实现 `read_file` / `write_file` / `list_dir`，统一返回 `ToolResult`；`write_file` 自动创建父目录
- **文件**：`src/forgeloop/tools/workspace.py`, `src/forgeloop/tools/fs_tools.py`, `tests/test_workspace_tools.py`
- **验证**：
  - 先写失败测试：`../` 逃逸被拒绝；读写圆跳；`list_dir` 含写入文件名
  - `pytest tests/test_workspace_tools.py` 通过
- **依赖**：Task 0
- **状态**：✓ completed · `f486eba`

## Task 3 — 护栏策略
- **目标**：危险命令识别 allow/deny/needs_approval
- **文件**：`src/forgeloop/guardrails/policy.py`, `tests/test_guardrails.py`
- **验证**：`rm -rf /` → deny；`pytest` → allow；`git push` → needs_approval
- **状态**：✓ completed · `f486eba`

## Task 4 — Shell 工具 + 分发器
- **目标**：统一 `ToolDispatcher`
- **文件**：`src/forgeloop/tools/shell_tool.py`, `dispatcher.py`, `tests/test_dispatcher.py`
- **验证**：未知工具错误；finish 短路
- **状态**：✓ completed · `f486eba`

## Task 5 — 反馈传感器 + 失败分类（重点）
- **目标**：解析 pytest 输出、分类、生成 FeedbackEvent
- **文件**：`src/forgeloop/feedback/sensor.py`, `classifier.py`, `tests/test_feedback.py`
- **验证**：构造失败输出 → assertion/import/syntax；`to_feedback` 结构化
- **状态**：✓ completed · `f486eba`

## Task 6 — 记忆存储 `[P]`
- **目标**：JSONL 记忆读写与检索
- **文件**：`src/forgeloop/memory/store.py`, `tests/test_memory.py`
- **验证**：写入后按关键词命中
- **状态**：✓ completed · `f486eba`

## Task 7 — 配置加载 `[P]`
- **目标**：YAML/默认 `HarnessConfig`
- **文件**：`src/forgeloop/config/loader.py`, `default.yaml`, `tests/test_config.py`
- **验证**：缺省可用；非法 `max_steps` 报错
- **状态**：✓ completed · `f486eba`

## Task 8 — Agent 主循环
- **目标**：组织上下文→LLM→护栏→工具→反馈回灌→停机
- **文件**：`src/forgeloop/loop/agent_loop.py`, `tests/test_agent_loop.py`
- **验证**：Mock write+finish；护栏 deny；失败反馈改变下一步
- **状态**：✓ completed · `f486eba`

## Task 9 — 凭据存储
- **目标**：keyring + 加密文件双后端；CLI
- **文件**：`src/forgeloop/credentials/store.py`, `cli.py`, `tests/test_credentials.py`
- **验证**：set/status/clear；status 无明文
- **状态**：✓ completed · `f486eba`

## Task 10 — 机制演示脚本
- **目标**：A.6 三类演示
- **文件**：`src/forgeloop/demo/mechanisms.py`, `tests/test_mechanism_demo.py`
- **验证**：演示退出码 0
- **状态**：✓ completed · `f486eba`

## Task 11 — FastAPI WebUI
- **目标**：任务、轨迹、HITL、凭据页
- **文件**：`src/forgeloop/api/*`, `tests/test_api.py`
- **验证**：mock 任务 succeeded
- **状态**：✓ completed · `9aebb1d`

## Task 12 — 分发与文档收尾
- **目标**：Dockerfile、README、GitHub Actions `unit-test`、Render 配置、冷启动修订
- **文件**：`Dockerfile`, `README.md`, `.github/workflows/ci.yml`, `render.yaml`, `SPEC_PROCESS.md`
- **验证**：CI job 名 `unit-test`；文档含公网部署步骤
- **状态**：✓ completed（本轮补齐 Actions + 冷启动修订）

---

## 完成追踪

| Task | Status | Commit |
|------|--------|--------|
| 0–11 | completed | 见上 |
| 12 | completed | 本轮 push |

验证命令：`make test` · `make demo` · `make run`
