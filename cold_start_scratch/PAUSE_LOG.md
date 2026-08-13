# Cold-start pause log (implementation attempt)

Recorded while implementing Task 1–2 from SPEC.md + PLAN.md only.
Rule: stop and ask — do not invent missing contracts.

| # | When | Ambiguity | Action taken |
|---|------|-----------|--------------|
| P1 | Start Task 1 | PLAN.md Task 1 body empty (only title + `[P]` + status) | Stopped using PLAN for acceptance; fell back to SPEC §3.2 / §6 |
| P2 | Define `LLMResponse` | SPEC names type but gives no fields | Did not invent schema; left TypedDict/dataclass stub with TODO + question |
| P3 | Define `LLMPort.complete(...)` | Signature: "messages + tool schema" — types, return shape, sync/async unspecified | Stub ABC with `*args/**kwargs` forbidden; marked incomplete |
| P4 | `MockLLM` script queue | Queue of what? `AgentAction`? `LLMResponse`? raw JSON strings? exhausted-queue behavior? | Queue of opaque `object` with explicit PAUSE comment |
| P5 | Structured action vs text | SPEC: "返回结构化动作或文本" — one type or union? how text maps to tools? | Not implemented discriminator |
| P6 | `LLMError` | Only "HTTP/鉴权错误包装"; no fields / base class | Minimal empty Exception subclass only |
| P7 | `AgentAction` fields | SPEC: `type/name, args, raw` — slash ambiguous (alias vs two fields) | Did not choose; see questions |
| P8 | Start Task 2 | PLAN.md Task 2 body empty | Same as P1 |
| P9 | `WorkspaceGate` API | Only behavioral rule: resolve paths, forbid `..` escape; no method names | Stub with one `resolve(rel)` documenting assumed name |
| P10 | Absolute paths / drive letters / symlinks | Unspecified (Windows noted as risk in §11) | Not implemented; questions filed |
| P11 | Tool return type | Table says "内容或错误" / "ok / error"; §6 has `ToolResult` | Unclear if tools return `ToolResult` or raise | Partial: return simple dict marked provisional |
| P12 | `list_dir` depth / metadata | "条目列表" — names only? file type? recursive? | Names-only non-recursive provisional |
| P13 | Package import path | Scratch vs `forgeloop.*` production layout | Used `cold_start_scratch.*` local packages to avoid touching `src/` |

**Verdict so far:** Cannot complete production-faithful Task 1–2 without human answers to Q1–Q8+ in REPORT.md.
