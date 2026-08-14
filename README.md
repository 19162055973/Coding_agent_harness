# ForgeLoop（Coding Agent Harness）

仓库：https://github.com/19162055973/Coding_agent_harness

自研 **Coding Agent Harness**：`Agent = LLM + Harness`。内核自己实现主循环、工具分发、治理护栏、反馈闭环、记忆与配置；**不以** LangChain AgentExecutor / AutoGen / CrewAI 等高层编排框架寄生。重点维度是**反馈闭环**（pytest 传感器 + 失败分类 + 回灌驱动下一步）。

## 项目简介

ForgeLoop 提供：

- 可注入的 `LLMPort`（MockLLM / OpenAI-compatible）
- 工作区路径围栏与工具（读写、shell、run_tests、finish）
- 代码级危险命令护栏与 HITL 审批钩子
- 确定性测试反馈与失败分类（可离线单测）
- WebUI 任务控制台 + CLI 凭据管理
- Docker / Render 分发；GitLab CI 与 GitHub Actions 均含 **`unit-test`** job

## 安装

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

## 运行

```bash
# 离线 Mock 模式（默认）
set FORGELOOP_USE_MOCK=1   # PowerShell: $env:FORGELOOP_USE_MOCK=1
make run
# 或
uvicorn forgeloop.api.app:app --host 0.0.0.0 --port 8000
```

浏览器打开：http://127.0.0.1:8000

```bash
# 机制演示（mock LLM，无网络）
make demo
# 测试
make test
```

## 分发命令（容器）

```bash
docker build -t forgeloop:latest .
docker run --rm -p 8000:8000 ^
  -e FORGELOOP_USE_MOCK=1 ^
  -e FORGELOOP_FORCE_FILE_CREDS=1 ^
  -e FORGELOOP_MASTER_PASSWORD=please-change ^
  forgeloop:latest
```

真实模型时：

```bash
docker run --rm -p 8000:8000 ^
  -e FORGELOOP_USE_MOCK=0 ^
  -e FORGELOOP_FORCE_FILE_CREDS=1 ^
  -e FORGELOOP_MASTER_PASSWORD=please-change ^
  -e FORGELOOP_API_KEY=YOUR_KEY ^
  -e FORGELOOP_API_BASE=https://api.openai.com/v1 ^
  -e FORGELOOP_MODEL=gpt-4o-mini ^
  forgeloop:latest
```



## Key 安全配置

| 方式 | 命令 / 做法 | 风险说明 |
|------|-------------|----------|
| OS 钥匙串（推荐本机） | `forgeloop creds set` | Windows Credential Manager / macOS Keychain / Secret Service |
| 加密文件（Docker/无钥匙串） | 设 `FORGELOOP_MASTER_PASSWORD` 后 `forgeloop creds set` | 主密码需另行保护 |
| `.env`（可选来源） | 复制 `.env.example` → `.env` | **明文磁盘 + 进程环境可见**，仅建议本地临时 |
| 状态查看 | `forgeloop creds status` | 仅 backend + 末四位掩码，不回显明文 |
| 清除 | `forgeloop creds clear` | |

## 目录结构

```
SPEC.md / PLAN.md / SPEC_PROCESS.md / AGENT_LOG.md / REFLECTION.md
src/forgeloop/
  loop/           # 主循环（harness 内核）
  llm/            # LLM 抽象 + Mock + OpenAI-compatible
  tools/          # 工作区围栏与工具分发
  guardrails/     # 危险动作护栏
  feedback/       # 测试传感器与失败分类（重点）
  memory/         # 会话记忆
  config/         # 声明式配置
  credentials/    # 凭据存储
  api/            # FastAPI WebUI
  demo/           # 机制演示
tests/            # mock-LLM 确定性单测
Dockerfile
.gitlab-ci.yml
```

## 安全边界说明

- Agent 只能访问给定 **workspace**；`..` 逃逸会被 `WorkspaceGate` 拒绝。
- `rm -rf /` 等危险 shell 由 **代码护栏** 拒绝（不是提示词）。
- `git push` / `pip install` 等可配置为 HITL `needs_approval`。
- 默认 WebUI 使用 MockLLM，不消耗配额、不触网。
- 仓库与镜像中不得包含真实 API Key。

## 已知限制

- 目标平台：Linux / Windows / macOS；容器以 `linux/amd64` 为主。
- 本机若无 Docker，可用 `pip install` + `uvicorn` 运行；CI 负责镜像构建校验。
- 真实 LLM 输出偶发非 JSON 时，循环会注入一次纠错提示；仍可能失败。
- 公网部署需自行托管（Render / Railway / Fly.io 等）并配置密钥。

## 第三方许可证

- FastAPI / Starlette / Uvicorn — MIT
- httpx — BSD
- Pydantic — MIT
- PyYAML — MIT
- keyring — MIT / PSF
- cryptography — Apache-2.0 / BSD
- pytest — MIT

## CI

- GitLab：`.gitlab-ci.yml` → job 名 **`unit-test`**
- GitHub Actions：`.github/workflows/ci.yml` → job 名 **`unit-test`**  
  - Actions 总览：https://github.com/19162055973/Coding_agent_harness/actions  
  - **已通过 run（unit-test Success）**：https://github.com/19162055973/Coding_agent_harness/actions/runs/31665240621  
  - Badge：![CI](https://github.com/19162055973/Coding_agent_harness/actions/workflows/ci.yml/badge.svg)

## 线上 WebUI

- **本机（已验证）**：http://127.0.0.1:8000 （`make run` / uvicorn）
- **公网（当前可访问，localtunnel 演示）**：https://wise-pigs-open.loca.lt  
  - `/health` 已验证返回 `{"ok":true,"service":"forgeloop"}`  
  - **注意**：隧道依赖本机 uvicorn + localtunnel 进程；关机后失效。


```bash
uvicorn forgeloop.api.app:app --host 0.0.0.0 --port $PORT
# 环境变量：FORGELOOP_USE_MOCK=1
```

