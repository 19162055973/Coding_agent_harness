from __future__ import annotations

import os
import tempfile
import threading
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from forgeloop.config.loader import load_config
from forgeloop.credentials.store import CredentialStore
from forgeloop.llm.mock import MockLLM
from forgeloop.llm.openai_compat import OpenAICompatLLM
from forgeloop.loop.agent_loop import AgentLoop
from forgeloop.memory.store import MemoryStore
from forgeloop.models import AgentAction, AgentTask, RunStatus

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="ForgeLoop", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

_lock = threading.Lock()
_tasks: dict[str, dict[str, Any]] = {}
_memory = MemoryStore(Path(tempfile.gettempdir()) / "forgeloop_memory.jsonl")


def _build_llm(use_mock: bool, script: list[AgentAction] | None = None):
    if use_mock or os.getenv("FORGELOOP_USE_MOCK", "1").lower() in {"1", "true", "yes"}:
        if script is not None:
            return MockLLM(script)
        # default demo script for UI smoke when mock
        return MockLLM(
            [
                AgentAction(name="list_dir", args={"path": "."}),
                AgentAction(
                    name="write_file",
                    args={
                        "path": "hello.py",
                        "content": "def hello():\n    return 'forge'\n",
                    },
                ),
                AgentAction(name="finish", args={"summary": "created hello.py (mock run)"}),
            ]
        )
    store = CredentialStore()
    key = store.get_key()
    if not key:
        raise RuntimeError("API key not configured")
    return OpenAICompatLLM(
        api_key=key,
        model=os.getenv("FORGELOOP_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("FORGELOOP_API_BASE", "https://api.openai.com/v1"),
    )


class TaskCreate(BaseModel):
    goal: str
    workspace: str | None = None
    max_steps: int = 10
    use_mock: bool = True


def _serialize_result(result) -> dict[str, Any]:
    steps = []
    for s in result.steps:
        steps.append(
            {
                "index": s.index,
                "action": {"name": s.action.name, "args": s.action.args},
                "guard": {"verdict": s.guard.verdict, "reason": s.guard.reason},
                "observation": s.observation,
                "feedback": asdict(s.feedback) if s.feedback else None,
            }
        )
    return {
        "status": result.status.value,
        "final_message": result.final_message,
        "steps": steps,
        "pending_action": (
            {"name": result.pending_action.name, "args": result.pending_action.args}
            if result.pending_action
            else None
        ),
    }


def _run_task(task_id: str, goal: str, workspace: str, max_steps: int, use_mock: bool) -> None:
    cfg = load_config()
    try:
        llm = _build_llm(use_mock=use_mock)
        loop = AgentLoop(llm=llm, config=cfg, memory=_memory)
        task = AgentTask(
            id=task_id,
            goal=goal,
            workspace=workspace,
            max_steps=max_steps,
            session_id=task_id,
        )
        result = loop.run(task)
        with _lock:
            _tasks[task_id]["result"] = _serialize_result(result)
            _tasks[task_id]["status"] = result.status.value
            _tasks[task_id]["pending_action"] = (
                {"name": result.pending_action.name, "args": result.pending_action.args}
                if result.pending_action
                else None
            )
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _tasks[task_id]["status"] = RunStatus.FAILED.value
            _tasks[task_id]["error"] = str(exc)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    creds = CredentialStore().status()
    with _lock:
        tasks = list(_tasks.values())[-20:]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "creds": creds,
            "tasks": list(reversed(tasks)),
            "use_mock_default": os.getenv("FORGELOOP_USE_MOCK", "1"),
        },
    )


@app.post("/api/tasks")
async def create_task(body: TaskCreate):
    task_id = str(uuid.uuid4())
    workspace = body.workspace or str(Path(tempfile.mkdtemp(prefix="forgeloop_ws_")))
    Path(workspace).mkdir(parents=True, exist_ok=True)
    with _lock:
        _tasks[task_id] = {
            "id": task_id,
            "goal": body.goal,
            "workspace": workspace,
            "status": RunStatus.RUNNING.value,
            "result": None,
            "pending_action": None,
            "error": None,
        }
    thread = threading.Thread(
        target=_run_task,
        args=(task_id, body.goal, workspace, body.max_steps, body.use_mock),
        daemon=True,
    )
    thread.start()
    thread.join(timeout=120)
    with _lock:
        return JSONResponse(_tasks[task_id])


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    with _lock:
        task = _tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(task)


@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    return _hitl(task_id, approve=True)


@app.post("/api/tasks/{task_id}/deny")
async def deny_task(task_id: str):
    return _hitl(task_id, approve=False)


def _hitl(task_id: str, approve: bool):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return JSONResponse({"error": "not found"}, status_code=404)
        pending = task.get("pending_action")
        workspace = task["workspace"]
        goal = task["goal"]
    if not pending:
        return JSONResponse({"error": "no pending action"}, status_code=400)
    cfg = load_config()
    llm = MockLLM([AgentAction(name="finish", args={"summary": "resumed after HITL"})])
    loop = AgentLoop(llm=llm, config=cfg, memory=_memory)
    action = AgentAction(name=pending["name"], args=pending.get("args") or {})
    result = loop.run(
        AgentTask(id=task_id, goal=goal, workspace=workspace, session_id=task_id),
        resume_approval=approve,
        pending_action=action,
    )
    # if approved, continue a bit more with mock finish already in resume path only
    with _lock:
        _tasks[task_id]["result"] = _serialize_result(result)
        _tasks[task_id]["status"] = result.status.value
        _tasks[task_id]["pending_action"] = None
        return JSONResponse(_tasks[task_id])


@app.get("/api/creds")
async def creds_status():
    st = CredentialStore().status()
    return {"configured": st.configured, "backend": st.backend, "hint_mask": st.hint_mask}


class CredsBody(BaseModel):
    api_key: str = Field(min_length=1)


@app.post("/api/creds")
async def creds_set(body: CredsBody):
    backend = CredentialStore().set_key(body.api_key.strip())
    return {"ok": True, "backend": backend}


@app.delete("/api/creds")
async def creds_clear():
    CredentialStore().clear()
    return {"ok": True}


@app.post("/ui/create")
async def ui_create(
    goal: str = Form(...),
    use_mock: str = Form("1"),
):
    body = TaskCreate(goal=goal, use_mock=use_mock in {"1", "true", "on", "yes"})
    await create_task(body)
    return RedirectResponse("/", status_code=303)


@app.get("/health")
async def health():
    return {"ok": True, "service": "forgeloop"}
