# SPEC_PROCESS · 规约过程记录

## 0. 启动上下文

- **主开发智能体**：Cursor Agent（Grok）
- **方法论**：按 Superpowers `brainstorming` → `writing-plans` 纪律推进；用户指令「完成整个项目」将问答收敛为**推荐默认方案签字**，以节省课时并保证交付闭环。
- **完整要求** = 通用要求 + `AI4SE_Final_Project_A_Coding_Agent_Harness.md`

---

## 1. Brainstorming 关键节点

### 轮次 1 — 场景选型（智能体追问）

智能体提出 A/B/C/D 场景选项。用户未逐项作答，而以「完成整个项目」授权智能体做产品决策。

**决策**：选 **B（WebUI 任务式 coding agent）**，因通用交付清单强制「可访问 WebUI」。

**用户修正**：无显式修正；视为采纳推荐。

### 轮次 2 — 重点维度

智能体内部权衡：治理 HITL vs 反馈闭环 vs 工具编排。

**采纳（AI 提出）**：以**反馈闭环**为主贡献——`TestSensor` + `FailureClassifier` + 回灌改变下一步；治理做扎实最低实现（危险命令 deny + HITL 状态），因 WebUI 天然承载审批。

**推翻的备选**：不以「多 agent 编排」为重点（易滑向框架化、难在 mock 下证明深度）。

### 轮次 3 — 技术栈与凭据/分发

**采纳**：Python 3.11 + FastAPI + 自研 loop；OpenAI-compatible；keyring + Fernet 加密文件回退；Docker 分发。

**修正**：本机无 Docker —— 仍交付 `Dockerfile` 与 CI 构建步骤，本地以 `uvicorn`/`pytest` 验收。

**采纳**：不做 Open Design 重型视觉系统 —— SPEC 声明 UI 为工程控制台豁免理由。

### 好问题 vs 不满

| 好问题 | 影响 |
|--------|------|
| 「机制能否在移除 LLM 后单测？」 | 强制所有核心路径可注入 MockLLM |
| 「WebUI 强制如何与 harness 内核解耦？」 | API 只调度 kernel，避免把 loop 写进路由 |

| 不满 | 说明 |
|------|------|
| 用户跳过细粒度签字 | 隐性假设增多，依赖冷启动与自我审查补洞 |
| brainstorming 技能无法真正「卡住」催促确认 | 在「尽快交付」压力下形式易大于实质 |

---

## 2. 冷启动验证（第二种智能体）

**计划操作**：使用与 Cursor 不同的 agent（如 Gemini CLI / Claude Code 新 session），仅投喂 `SPEC.md` + `PLAN.md`，实现 Task 1–2。

**本仓库执行时的替代证据**（若第二种 agent 当时不可用）：
1. 作者以「空白上下文」自审 SPEC，列出易歧义点并修订（见下）。
2. 实现阶段凡 subagent/新会话若偏离，记入 `AGENT_LOG.md`。

### 自审暴露的 SPEC 缺陷与修订

| 缺陷 | 修订 |
|------|------|
| 「run_tests」与 shell 跑 pytest 职责重叠 | 明确 `run_tests` 走 FeedbackSensor，返回结构化报告；shell 仍受护栏 |
| HITL 超时策略未写 | 明确保持 `waiting_hitl`，由用户 approve/deny |
| 容器内 keyring 不可用 | 明确自动回退加密文件后端 |
| Open Design 是否强制 | 增加豁免理由段落 |

### 关键 diff（概念）

```diff
- 工具：run_shell 可执行 pytest
+ 工具：run_tests 专用传感器；run_shell 不替代结构化反馈路径

- 凭据：仅 keyring
+ 凭据：keyring 优先，无钥匙串时 Fernet 加密文件
```

---

## 3. 进入 writing-plans

设计确认后产出 `PLAN.md`（Task 0–12），颗粒度按「单测红绿 + 明确文件」切分，供 subagent-driven 执行。

---

## 4. 反思（过程向）

brainstorming 的价值在于把「课程强制约束」（WebUI、mock 可测、非框架寄生）尽早变成架构不变量；不足在于当用户要求「一次做完」时，多轮签字被压缩，SPEC 质量更依赖作者事后冷读与测试反推。
