# Cold-Start Validation Report

## Agent role

**Independent cold-start agent** (second agent, no prior conversation history about this project).  
Workspace: `D:\courseResource\大三下\智能软件训练营\project`.  
Sources consulted for requirements: **only** `SPEC.md` and `PLAN.md`.  
Repo listing confirmed production `src/forgeloop/` already exists; **did not read or copy** those files.  
Artifacts created: `cold_start_scratch/**` (own minimal stubs + this report).

---

## Executive verdict

| Question | Answer |
|----------|--------|
| Are Task 1–2 implementable from SPEC+PLAN alone? | **partial** |
| Can a new implementer ship production-faithful code without guessing? | **No** |
| Was a complete Task 1 MockLLM + Task 2 file-tool stack finished in scratch? | **No** — stopped at documented pause points; only behavioral stubs |

**Why partial:** SPEC §3.2 / §3.3 / §6 give *module intent* and *tool table rows*, but omit concrete type contracts, method signatures, and acceptance tests. PLAN.md Task 1–2 bodies are effectively empty (title + parallel tag + status only), so they add **no** file list, verification steps, or TDD criteria for a cold start.

---

## Exact questions for the human

(At least three; these are the blockers that halted faithful implementation.)

1. **`LLMResponse` schema:** SPEC §6 lists the type name but no fields. What are the required fields (e.g. `action: AgentAction | None`, `text: str | None`, `raw: Any`)? Is the return always one object that may hold either structured action or free text?

2. **`LLMPort.complete` contract:** Exact signature? Are `messages` OpenAI-style `list[dict]`? What is “tool schema 描述” — JSON Schema list, custom dataclass, or string prompt appendix? Sync only or async? Does `complete` raise `LLMError` only for transport/auth, or also for parse failures?

3. **`MockLLM` script queue:** What is queued — `LLMResponse`, `AgentAction`, raw JSON strings, or callables `(messages) -> response`? What happens when the queue is empty (raise, return `finish`, return error observation)?

4. **`AgentAction` naming:** SPEC writes `type/name, args, raw`. Is that one field aliased as type-or-name, two fields `type` and `name`, or `name` (tool) plus optional `type` enum?

5. **`WorkspaceGate` public API:** Confirm method names (`resolve`? `safe_join`?), whether absolute paths are rejected vs remapped, symlink escape policy, and Windows drive-letter / case-folding rules.

6. **File tool returns:** Should `read_file` / `write_file` / `list_dir` return `ToolResult` (`ok, output, error` from §6), raise exceptions, or return bare strings/lists as the §3.3 table colloquially says?

7. **`write_file` parent directories:** If `a/b/c.txt` and `a/b` does not exist, create parents, fail, or require a prior tool call?

8. **`list_dir` semantics:** Non-recursive names only? Include file/dir type? Sort order? Default path when omitted?

9. **PLAN emptiness:** Task 1–2 in PLAN.md have no **目标 / 文件 / 验证** sections (unlike Task 0). Is that intentional compression after completion, or missing source-of-truth for implementers? If compressed, where should cold-start agents read the original task cards?

10. **Package layout for Task 1–2:** Confirm expected modules (`forgeloop.llm.base`, `mock.py`, `tools/workspace.py`, `fs_tools.py`, shared `models.py`?) — SPEC gives package names (`forgeloop.llm`, `forgeloop.tools`) but not file splits.

11. **Encoding / binary:** Text tools assume UTF-8 text only? Binary read/write in scope for Task 2?

12. **Acceptance tests for Task 1–2:** PLAN says every step includes “先写失败测试”, but Task 1–2 give no test names or assertions. What minimal pytest cases must go green before Task 1 / Task 2 are “done”?

---

## Pause points (chronological)

See also `cold_start_scratch/PAUSE_LOG.md`.

| ID | Pause |
|----|-------|
| P1 | PLAN Task 1 body empty → cannot derive acceptance from PLAN |
| P2 | `LLMResponse` fields missing → refused to invent dataclass |
| P3 | `complete(...)` types unspecified → ABC stub only |
| P4 | Mock queue element type / empty behavior unspecified |
| P5 | “结构化动作或文本” discriminator unspecified |
| P6 | `LLMError` shape unspecified |
| P7 | `AgentAction` `type/name` slash ambiguous |
| P8 | PLAN Task 2 body empty |
| P9 | `WorkspaceGate` method names not specified (used provisional `resolve`) |
| P10 | Absolute paths / symlinks / Windows paths unspecified |
| P11 | Tool return vs `ToolResult` mismatch between §3.3 table and §6 |
| P12 | `list_dir` depth/metadata unspecified |
| P13 | Scratch package naming vs production `forgeloop.*` |

**Guess explicitly flagged in scratch code:** `write_file` calls `mkdir(parents=True)` — **not** justified by SPEC; recorded as a guess that should be confirmed or removed (Q7).

---

## Misreadings vs likely author intent

| Possible misreading (if one “guesses”) | Likely author intent (inferred, not used as authority) |
|----------------------------------------|--------------------------------------------------------|
| PLAN Task 1–2 being blank means “free design” | More likely: tasks were completed and PLAN was condensed to status; real cards lived in chat/`AGENT_LOG`/earlier PLAN revision — **cold-start cannot rely on that** |
| §3.3 table “内容或错误” means return `str` | §6 `ToolResult` suggests structured results; table is informal |
| `type/name` means two required fields | Common harness pattern is a single tool `name` + `args`; “type/name” may be sloppy wording for “action kind / tool name” |
| MockLLM must call a real HTTP client behind a flag | SPEC: tests禁止触网; Mock is scripted — no network |
| WorkspaceGate only string-checks for `..` | SPEC says resolve then forbid escape past root — resolve+`relative_to` is the natural reading |
| Task 1 includes OpenAI HTTP client | SPEC lists real OpenAI-compatible as part of `forgeloop.llm`, but PLAN title is “LLM 抽象 + MockLLM”; real client might be same task or later — **ambiguous** |

---

## Gaps: SPEC vs what a new implementer needs

### Critical gaps

- **PLAN Task 1–2 lack** 目标 / 文件 / 验证 / 依赖 — Task 0 still has them; asymmetry blocks subagent decomposition.
- **Data model incompleteness:** `LLMResponse` named but undefined; `AgentAction` field grammar ambiguous; `HarnessConfig` “见配置字段” with no field list in §6.
- **No JSON action schema example** despite §11 risk “严格 JSON action schema”.
- **No interface sketch** (Protocol/ABC signatures) for `LLMPort`, `WorkspaceGate`, tools.
- **No Task-level test plan** linking SPEC acceptance (§10) down to Task 1–2 (机制演示/护栏 are later tasks).

### Moderate gaps

- Encoding, mkdir-parents, symlink, Windows path policy.
- Whether Task 1 ships only Mock or also `openai_compat` client.
- Observation string format when tools fail (needed by later loop, but affects Task 2 return shape).

### What *is* enough to start stubs

- Package areas: `forgeloop.llm`, `forgeloop.tools`.
- MockLLM = scripted predetermined actions; no network in tests.
- Tools: `read_file`, `write_file`, `list_dir` + path gate against workspace escape.
- Shared names: `LLMError`, `ToolResult`, `AgentAction`, `WorkspaceGate`.

---

## Scratch attempt summary

Created under `cold_start_scratch/` (not `src/`):

| Path | Intent |
|------|--------|
| `llm/base.py` | `LLMPort` ABC, `MockLLM` opaque queue, `LLMResponse` **hard-stops** with `NotImplementedError` |
| `tools/workspace.py` | Provisional `WorkspaceGate.resolve` with escape check |
| `tools/fs_tools.py` | Provisional dict returns for read/write/list |
| `smoke_probe.py` | Local probes (not claimed as PLAN verification) |
| `PAUSE_LOG.md` | Pause ledger |

**Not done (by rule):** inventing full schemas; copying `src/forgeloop`; modifying SPEC/PLAN/production src.

---

## Suggested SPEC/PLAN wording fixes (report-only diffs)

### PLAN.md — restore Task 1–2 cards

```diff
 ## Task 1 — LLM 抽象 + MockLLM `[P]`
-- **状态**：✓ completed
+- **目标**：定义 `LLMPort` / `LLMResponse` / `LLMError`；实现按脚本队列吐出预定动作的 `MockLLM`；单测不触网
+- **文件**：`src/forgeloop/llm/base.py`, `src/forgeloop/llm/mock.py`, `src/forgeloop/models.py`（共享模型）, `tests/test_llm_mock.py`
+- **验证**：
+  - 先写失败测试：队列按序返回预定 `LLMResponse`；队列耗尽抛约定异常；不发起 HTTP
+  - `pytest tests/test_llm_mock.py` 通过
+- **依赖**：Task 0
+- **状态**：✓ completed
 
 ## Task 2 — WorkspaceGate + 文件工具 `[P]`
-- **状态**：✓ completed
+- **目标**：`WorkspaceGate` 解析相对路径并拒绝逃逸；实现 `read_file` / `write_file` / `list_dir`，统一返回 `ToolResult`
+- **文件**：`src/forgeloop/tools/workspace.py`, `src/forgeloop/tools/fs_tools.py`, `tests/test_workspace_tools.py`
+- **验证**：
+  - 先写失败测试：`../` 与绝对越界路径被拒绝；读写圆跳；`list_dir` 返回排序后的名字列表
+  - `pytest tests/test_workspace_tools.py` 通过
+- **依赖**：Task 0
+- **状态**：✓ completed
```

### SPEC.md §6 — complete core types

```diff
 ## 6. 数据模型
 
 - `AgentTask`：id, goal, workspace, max_steps, status
-- `AgentAction`：type/name, args, raw
+- `AgentAction`：name (工具名 str), args (dict), raw (原始 LLM 载荷, optional)
+- `LLMResponse`：action (AgentAction | None), text (str | None), raw (Any)
+  - 不变量：`action` 与 `text` 至少其一非空；工具轮次优先填 `action`
 - `GuardDecision`：allow | deny | needs_approval, reason
 - `ToolResult`：ok, output, error
```

### SPEC.md §3.2 — pin port + mock

```diff
 ### 3.2 LLM 抽象（`forgeloop.llm`）
 
 | 项 | 说明 |
 |----|------|
-| 输入 | messages + tool schema 描述 |
-| 行为 | `LLMPort.complete(...)` 返回结构化动作或文本；`MockLLM` 按脚本队列吐出预定动作 |
-| 输出 | `LLMResponse` |
+| 输入 | `messages: list[dict]`（role/content）；`tools: list[dict]`（OpenAI-compatible tool/function schema，可空） |
+| 行为 | `LLMPort.complete(messages, tools) -> LLMResponse`；`MockLLM(script: Sequence[LLMResponse])` 按 FIFO 弹出；队列空则抛 `LLMError("mock script exhausted")` |
+| 输出 | `LLMResponse`（见 §6） |
 | 边界 | 真实供应商仅 OpenAI-compatible Chat Completions；测试禁止触网 |
 | 错误 | HTTP/鉴权错误包装为 `LLMError` |
```

### SPEC.md §3.3 — pin gate + ToolResult + mkdir policy

```diff
 路径一律经 `WorkspaceGate` 解析，禁止 `..` 逃逸出 workspace root。
+
+`WorkspaceGate.resolve(relative: str) -> Path`：
+- 拒绝绝对路径与空路径；
+- 以 `Path(root, relative).resolve()` 后要求结果位于 `root` 之下（含 symlink 解析后仍须在 root 内）；
+- Windows 下对 root 与结果做 `resolve()` 后再比较。
+
+文件工具一律返回 `ToolResult`。`write_file` 若父目录不存在则 `ok=False`（不自动 `mkdir -p`），由 agent 显式创建目录策略另行规定。
+`list_dir`：非递归，返回排序后的 basename 字符串列表于 `ToolResult.output`。
```

*(Above mkdir policy is an example clarification — human must pick create-parents vs fail; scratch currently guessed create-parents.)*

---

## Implementability scorecard

| Task | From SPEC alone | From PLAN alone | SPEC+PLAN together |
|------|-----------------|-----------------|--------------------|
| Task 1 LLM Mock | partial (behavior yes, types no) | **no** (empty card) | **partial** |
| Task 2 Workspace + fs tools | partial (escape rule + tool names yes; API/returns thin) | **no** (empty card) | **partial** |

**Overall: partial** — a disciplined implementer can scaffold directories and escape checks, but cannot finish a SPEC-faithful, testable Task 1–2 without answering the questions above or restoring PLAN task cards / SPEC field definitions.

---

## Process notes

- No network used.
- Did not modify `SPEC.md`, `PLAN.md`, or production `src/`.
- Did not read `src/forgeloop/**` contents for this validation.
- Cold-start rule “STOP on ambiguity” was applied: `LLMResponse` construction hard-fails; Mock empty-queue hard-fails; several APIs marked provisional.
