# SPEC · ForgeLoop Coding Agent Harness

> Spec-Driven, Subagent-Built, Human-Owned.  
> 版本：1.0 · 日期：2026-08-10

---

## 1. 问题陈述

**问题**：现成编码智能体把「主循环 / 治理 / 反馈」藏在黑盒里，学生与工程师难以理解、验证与定制「Agent = LLM + Harness」中 harness 这一层。当需要确定性护栏、可测试的反馈闭环、以及可审计的 HITL 时，提示词无法替代工程实现。

**目标用户**：
- 想学习 / 演示 coding agent 内核机制的学生与工程师；
- 需要在受限工作区内跑「改代码 → 跑测试 → 自我修正」任务，并要求危险命令人工审批的个人开发者。

**为何值得做**：交付一个**自研 harness 内核**（非 LangChain AgentExecutor 等高层编排），六个维度均可运行，并以**反馈闭环**作为主贡献——移除真实 LLM 后，机制仍可用 mock LLM 确定性单测验证。同时满足课程对凭据安全、容器分发、WebUI 与 GitLab CI 的工程要求。

---

## 2. 用户故事（INVEST）

1. **作为**开发者，**我希望**在 WebUI 提交「在工作区内修改代码并通过测试」的任务，**以便**观察 agent 多轮工具调用与自我修正过程。
2. **作为**开发者，**我希望**危险 shell（如 `rm -rf`、写工作区外路径）被代码护栏拦截并进入 HITL 审批，**以便**不会因模型幻觉造成不可逆损失。
3. **作为**开发者，**我希望**测试失败被解析为结构化反馈并回灌下一轮上下文，**以便**agent 根据客观信号修正而非凭空猜测。
4. **作为**运维者，**我希望**API Key 存入 OS 钥匙串或主密码加密文件，且状态查看不回显明文，**以便**符合凭据治理要求。
5. **作为**贡献者，**我希望**用 mock LLM 一键跑通单元测试与机制演示，**以便**离线验证护栏、反馈与停机逻辑。
6. **作为**使用者，**我希望**通过 Docker 单条命令启动并安全配置自己的 key，**以便**在全新机器上复现。

---

## 3. 功能规约（按模块）

### 3.1 Agent 主循环（`forgeloop.loop`）

| 项 | 说明 |
|----|------|
| 输入 | `AgentTask`（目标文本、工作区路径、最大步数、配置） |
| 行为 | 组织上下文 → 调用 `LLMPort` → 解析 `AgentAction` → 护栏检查 → 工具分发 → 可选反馈传感器 → 回灌 → 停机判断 |
| 输出 | `AgentRunResult`（状态、轨迹、最终消息） |
| 边界 | 步数耗尽 / 显式 `finish` / HITL 等待 / 不可恢复错误 |
| 错误 | LLM 解析失败计入轨迹并注入纠错提示；工具异常捕获为 observation |

### 3.2 LLM 抽象（`forgeloop.llm`）

| 项 | 说明 |
|----|------|
| 输入 | messages + tool schema 描述 |
| 行为 | `LLMPort.complete(...)` 返回结构化动作或文本；`MockLLM` 按脚本队列吐出预定动作 |
| 输出 | `LLMResponse` |
| 边界 | 真实供应商仅 OpenAI-compatible Chat Completions；测试禁止触网 |
| 错误 | HTTP/鉴权错误包装为 `LLMError` |

### 3.3 工具分发（`forgeloop.tools`）

| 工具 | 输入 | 行为 | 输出 |
|------|------|------|------|
| `read_file` | 相对路径 | 读取工作区内文件 | 内容或错误 |
| `write_file` | 相对路径 + 内容 | 写入工作区（禁止逃逸） | ok / error |
| `list_dir` | 相对路径 | 列出目录 | 条目列表 |
| `run_shell` | 命令字符串 | 在工作区 cwd 执行（受护栏） | stdout/stderr/exit |
| `run_tests` | 可选参数 | 调用反馈传感器跑测试 | 结构化 `TestReport` |
| `finish` | 摘要 | 请求停机 | 结束 run |

路径一律经 `WorkspaceGate` 解析，禁止 `..` 逃逸出 workspace root。

### 3.4 治理护栏（`forgeloop.guardrails`）

| 项 | 说明 |
|----|------|
| 输入 | 待执行 `AgentAction` |
| 行为 | 规则匹配：危险命令模式、工作区外写、禁止网络类命令（可配置）；命中则 `blocked` 或 `needs_approval` |
| 输出 | `GuardDecision` |
| 边界 | HITL：WebUI / API 提供 approve/deny；超时保持 `waiting_hitl` |
| 错误 | 未知工具名直接拒绝 |

**危险模式（默认）**：`rm -rf`、`rm -r /`、`del /s`、`format `、`mkfs`、`dd if=`、`shutdown`、`reboot`、`curl | sh`、写 `/etc`、以及任何解析后路径落在 workspace 外的写操作。

### 3.5 反馈闭环（重点维度）（`forgeloop.feedback`）

| 项 | 说明 |
|----|------|
| 输入 | 工作区 + 测试命令（默认 `python -m pytest -q`） |
| 行为 | 执行测试 → 解析通过/失败 → `FailureClassifier` 分类（assertion / import / syntax / unknown）→ 生成 `FeedbackEvent` 注入下一轮 |
| 输出 | 结构化反馈文本 + 分类标签 |
| 边界 | 连续同类失败达到阈值可触发「换策略」提示；最大修正轮次受 `max_steps` 约束 |
| 错误 | 测试命令不存在时返回明确 sensor 错误，不伪装为测试失败 |

### 3.6 记忆（`forgeloop.memory`）

| 项 | 说明 |
|----|------|
| 输入 | 会话 id、键值笔记、决策摘要 |
| 行为 | 本地 JSONL / SQLite 文件存储；按需检索最近 N 条与关键词匹配条目注入 system 附加上下文 |
| 输出 | `MemoryHits` |
| 边界 | 不接第三方 memory 框架；单会话默认隔离，可选 `project` 级共享笔记 |
| 错误 | 损坏文件时重建空库并记录告警 |

### 3.7 配置（`forgeloop.config`）

| 项 | 说明 |
|----|------|
| 输入 | `forgeloop.yaml`（或默认内置） |
| 行为 | 声明 max_steps、测试命令、危险正则、HITL 开关、模型名、workspace 策略 |
| 输出 | `HarnessConfig` |
| 边界 | 配置是内容物；校验 schema，非法字段失败快 |

### 3.8 凭据（`forgeloop.credentials`）

| 项 | 说明 |
|----|------|
| 录入 | CLI `forgeloop creds set` 隐藏输入；WebUI 仅写、不回显 |
| 存储 | 优先 OS keyring；Docker/无钥匙串时使用 Fernet + 主密码派生密钥的加密文件 `~/.forgeloop/secrets.enc` |
| 查看 | `forgeloop creds status` 仅显示是否已配置 / 后端类型 / 末四位掩码 |
| 更新/清除 | `set` 覆盖；`clear` 删除 |
| 环境变量 | 支持从 `.env` 的 `FORGELOOP_API_KEY` 加载作为**来源之一**，但文档声明明文与进程环境可见风险；生产推荐 keyring/加密文件 |

### 3.9 WebUI / API（`forgeloop.api`）

| 端点 | 行为 |
|------|------|
| `GET /` | 任务控制台：提交任务、看轨迹、HITL 审批、凭据状态 |
| `POST /api/tasks` | 创建任务并异步/同步跑 harness |
| `GET /api/tasks/{id}` | 查询状态与轨迹 |
| `POST /api/tasks/{id}/approve` | HITL 批准 |
| `POST /api/tasks/{id}/deny` | HITL 拒绝 |
| `GET/POST /api/creds` | 状态 / 设置（不回显） / 清除 |

---

## 4. 非功能性需求

- **性能**：单次工具超时默认 60s；mock 路径单测套件 < 30s。
- **安全**：见 §7 威胁模型；工作区沙箱路径围栏；默认不启用任意外网 shell。
- **可用性**：WebUI 可展示步骤轨迹；CLI 可跑 demo 与 creds。
- **可观测性**：每步记录 action / observation / guard decision / feedback；可导出 JSON 轨迹。

---

## 5. 系统架构

```
Browser WebUI ──HTTP──▶ FastAPI
                          │
                          ▼
                   AgentLoop (harness kernel)
          ┌───────────┼───────────┬────────────┬──────────┐
          ▼           ▼           ▼            ▼          ▼
       LLMPort    Tools      Guardrails    Feedback    Memory
      (mock/real) Dispatcher  (HITL)       Sensor      Store
          │           │
          │           ▼
          │      WorkspaceGate
          ▼
     OpenAI-compatible API (optional)
```

**数据流**：User task → Loop 组装 messages（config + memory hits + history）→ LLM 产出 action → Guard → Tool →（若 `run_tests`）Feedback 回灌 → 直至 finish/HITL/limit。

**外部依赖**：可选 OpenAI-compatible LLM；pytest 作为默认反馈传感器命令；OS keyring 或加密文件。

---

## 6. 数据模型

- `AgentTask`：id, goal, workspace, max_steps, status
- `AgentAction`：type/name, args, raw
- `GuardDecision`：allow | deny | needs_approval, reason
- `ToolResult`：ok, output, error
- `TestReport`：passed, failed, failures[], raw
- `FeedbackEvent`：kind, classification, summary, raw_ref
- `MemoryEntry`：id, session_id, kind, text, created_at
- `AgentStep`：index, action, guard, result, feedback?
- `AgentRunResult`：status, steps[], final_message
- `HarnessConfig`：见配置字段
- `CredentialStatus`：configured, backend, hint_mask

---

## 7. 凭据与分发设计

### 7.1 威胁模型与对策

| 威胁 | 对策 |
|------|------|
| Key 硬编码进仓库 | 代码审查 + `.gitignore`；CI 不含密钥 |
| Key 进 shell history | 禁止文档推荐 `export`；CLI 用 getpass；`.env` 不提交 |
| `.env` 明文 / 进程环境可见 | 文档明示风险；优先 keyring；容器用加密文件或运行时注入且不写镜像层 |
| 日志回显 | status 仅掩码；禁止 print key |
| 容器逃逸读宿主机 keyring | 容器默认用加密文件后端，主密码经 env/`docker run -e` 注入且不入镜像 |

### 7.2 分发

- **形态**：OCI 容器（主）+ `pip install -e .` 开发安装。
- **获取**：`docker build -t forgeloop .` → `docker run -p 8000:8000 -v workspace:/workspace forgeloop`
- **目标机 key**：`docker exec` 内 `forgeloop creds set`（加密文件）或挂载已有 secrets；宿主机开发用 keyring。
- **已知限制**：无 Docker 时可 `uvicorn` 本地跑；keyring 在无图形/无 Secret Service 的 Linux 上可能不可用，自动回退加密文件。

---

## 8. 技术选型与理由

| 选型 | 理由 |
|------|------|
| Python 3.11 | 测试生态好、keyring/FastAPI 成熟、课程交付快 |
| FastAPI + Jinja2 WebUI | 满足强制 WebUI；实现薄、可部署 |
| 自研 loop（非 LangChain Agent） | 满足 A.4 实现边界 |
| httpx + OpenAI-compatible | 供应商可替换，仅用补全 API |
| pytest | TDD 与反馈传感器一致 |
| keyring + cryptography.Fernet | 安全存储双后端 |
| Docker | 通用要求分发 |
| 未使用 Open Design | UI 为轻量控制台而非营销站；在 SPEC 声明豁免理由：交互以轨迹/审批为主，采用简洁自研样式 |

**重点维度**：反馈闭环——确定性 `TestSensor` + `FailureClassifier` + 回灌驱动下一步；机制演示覆盖护栏拦截、失败注入后动作改变、分类器行为。

---

## 9. 领域与机制设计（A.5）

| 类别 | 设计 | 编码落点 |
|------|------|----------|
| 动作/工具 | 读写列目录、shell、跑测试、finish | `tools/*` + `WorkspaceGate` |
| 客观反馈 | pytest 退出码与失败节点解析 | `feedback/sensor.py`, `classifier.py` |
| 危险动作 | 危险 shell / 路径逃逸 → deny 或 HITL | `guardrails/policy.py` + API approve |
| 记忆 | 会话笔记与决策摘要按需检索 | `memory/store.py` |
| **重点** | 反馈闭环：失败分类 + 回灌改变后续动作 | mock 演示脚本可证明 |

判定标准：所有上述机制在 MockLLM 下单测可绿，不依赖网络。

---

## 10. 验收标准

1. `make test`（或 `pytest`）全部通过，含 mock-LLM 机制测试。
2. `python -m forgeloop.demo.mechanisms` 打印三类确定性演示成功。
3. 危险 `rm -rf /` 类动作被护栏拦截（单测断言）。
4. 注入测试失败后，下一步动作与失败前不同（演示/单测）。
5. 凭据 set/status/clear 可用，status 无明文。
6. WebUI 可创建任务、查看轨迹、处理 HITL。
7. Dockerfile 可构建；README 含获取/运行/key/限制。
8. `.gitlab-ci.yml` 含 `unit-test` job。

---

## 11. 风险与未决问题

- 真实 LLM 输出格式漂移 → 严格 JSON action schema + 修复重试一轮。
- Windows 与 Linux 路径/命令差异 → WorkspaceGate 统一；演示以 Python/pytest 为主。
- 无 Docker 环境无法本地验镜像 → CI 构建；README 提供纯 Python 路径。
- 公网部署需用户自备 LLM key 与托管平台账号。
- 冷启动验证需「第二种智能体」——过程记入 `SPEC_PROCESS.md`；若课时压缩，以文档化缺陷修复为准。
