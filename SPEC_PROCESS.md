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

## 2. 冷启动验证（第二种智能体）— 客观证据

**时间**：2026-08-12  
**第二种智能体**：独立 Cursor `generalPurpose` 新会话（与主开发会话隔离，无共享对话历史）  
**输入约束**：仅允许阅读 `SPEC.md` + `PLAN.md`；禁止复制 `src/forgeloop`；不确定即暂停提问  
**指定范围**：PLAN Task 1–2  
**产物**：`cold_start_scratch/`（桩代码 + `REPORT.md` + `PAUSE_LOG.md`）

### 2.1 智能体在何处暂停并提问（节选）

1. `LLMResponse` 字段未定义 → 拒绝臆造 dataclass  
2. `LLMPort.complete` 签名 / messages 形态不明 → 只留 ABC stub  
3. `MockLLM` 队列元素类型与耗尽行为不明  
4. `AgentAction` 的 `type/name` 斜杠写法歧义  
5. PLAN Task 1–2 卡片被压缩成仅「状态：completed」，无目标/文件/验证 → **无法从 PLAN 单独开工**  
6. 文件工具返回值：§3.3 口语「内容或错误」vs §6 `ToolResult`  
7. `write_file` 是否自动 `mkdir -p`  
8. `list_dir` 深度与排序  

完整 12+ 个 pause 见 `cold_start_scratch/REPORT.md`。

### 2.2 与原意不一致的解读

| 冷启动解读 | 判定 | 处理 |
|------------|------|------|
| PLAN 空白 = 可自由设计接口 | **SPEC/PLAN 写残（作者过早压缩）**，不是 agent 读错 | 恢复 Task 1–2 完整卡片 |
| `type/name` = 两个必填字段 | **SPEC 措辞含糊**；实现本意是单一 `name` | SPEC 改为 `name` + `args` + `raw?` |
| 工具返回裸字符串 | 表格口语化导致误读；模型层应是 `ToolResult` | SPEC 表格改为明确 `ToolResult` |
| `write_file` 不建父目录 | 合理暂停点；实现选择自动建父目录 | SPEC 写死「自动创建缺失父目录」 |

### 2.3 产出与预期差距

- 预期：第二种 agent 能独立完成 Task 1–2 红绿。  
- 实际：**partial** — 能搭目录与逃逸检查骨架，但无法在不猜测的前提下完成可测实现。  
- 结论：实现完成后把 PLAN 压成状态表，会毁掉冷启动可用性；SPEC 数据模型必须把 `LLMResponse` 等写全。

### 2.4 据此对 SPEC / PLAN 的修订（关键 diff）

```diff
 ### 3.2 LLM 抽象
-| 输入 | messages + tool schema 描述 |
-| 行为 | LLMPort.complete(...) 返回结构化动作或文本；MockLLM 按脚本队列…
+| 输入 | messages: list[LLMMessage]；tools_desc: str
+| 行为 | complete(...) -> LLMResponse；MockLLM FIFO；队列空抛 LLMError
+| JSON 约定 | {"name": "<tool>", "args": {...}}

 ### 3.3
-| write_file | … | ok / error |
+| write_file | … | ToolResult；自动创建缺失父目录 |
+ WorkspaceGate.resolve(rel) 语义写清

 ## 6 数据模型
-- AgentAction：type/name, args, raw
+- AgentAction：name, args, raw?
+- LLMResponse：content, action?
+- HarnessConfig 字段列表写全

 ## PLAN Task 1–2
-- 仅「状态：✓ completed」
+- 恢复 目标 / 文件 / 验证 / 依赖（冷启动后回填）
```

### 2.5 反思

这次冷启动证明：共享隐性上下文会让主 agent「以为 PLAN 已足够」。第二种 agent 在空白 Task 卡上立刻停住——这正是课程要的信号。修订后 Task 1–2 对陌生实现者应达到「可不提问完成 stubs + 测试」的清晰度。

---

## 3. 进入 writing-plans

设计确认后产出 `PLAN.md`（Task 0–12）。冷启动后已把压缩掉的 Task 1–2 卡片恢复。

---

## 4. 过程向反思

brainstorming 的价值在于把课程硬约束写成架构不变量；不足在于交付压力下签字与 PLAN 维护被压缩。冷启动是单人项目里最接近同侪评审的机制，本项目在实现后补做，成本是返工文档——但仍比没有客观证据更好。
