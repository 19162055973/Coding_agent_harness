# Agent Log · ForgeLoop

按时间顺序记录关键节点。格式：时间 | Task | 技能/动作 | 摘要

---

## 2026-08-10 · 启动

- **技能**：brainstorming（方法论对齐）→ writing-plans
- **决策**：产品 = WebUI 任务式 coding agent；重点 = 反馈闭环；栈 = Python/FastAPI；分发 = Docker
- **人工**：用户授权「完成整个项目」，跳过逐轮多选确认；人工锁定上述默认
- **产物**：`SPEC.md`, `PLAN.md`, `SPEC_PROCESS.md`
- **教训**：课程硬约束（WebUI、mock 单测、自研 loop）应在第一轮就写成不变量，避免后期返工

---

## 2026-08-10 · 实现推进

- **技能**：test-driven-development + subagent-driven-development（同会话按 Task 切片执行）
- **偏离**：未对每个 Task 开独立 git worktree/PR（单人课时与环境限制）；在 `AGENT_LOG` 记录偏离理由，仍按 Task 顺序红绿重构并分 commit
- **上下文**：禁止使用 LangChain AgentExecutor 等高层循环；LLM 仅补全 API

---

## 2026-08-10 · 验收

- **验证**：`python -m pytest -q` → **25 passed**
- **机制演示**：`python -m forgeloop.demo.mechanisms` → 护栏拦截 / 反馈改动作 / 分类器 均 OK
- **人工修改**：修复 `run_tests` 双次执行；为 `TestSensor`/`TestFailure` 加 `__test__=False` 避免 pytest 误收集；HITL resume 路径对齐反馈传感器
- **教训**：反馈路径必须独占 `TestSensor`，否则「机制」会退化成 shell 输出拼进 prompt

---

## 2026-08-10 · 分发与文档

- **产物**：`Dockerfile`, `.gitlab-ci.yml`（job: `unit-test`）, `README.md`, `REFLECTION.md`
- **部署**：本机可 `make run`；公网 URL 需推送到托管平台后回填 README
