from pathlib import Path

from forgeloop.models import AgentAction
from forgeloop.tools.dispatcher import ToolDispatcher
from forgeloop.tools.workspace import WorkspaceGate


def test_dispatcher_unknown(tmp_path: Path):
    d = ToolDispatcher(WorkspaceGate(tmp_path))
    r = d.dispatch(AgentAction(name="nope", args={}))
    assert not r.ok


def test_dispatcher_finish(tmp_path: Path):
    d = ToolDispatcher(WorkspaceGate(tmp_path))
    r = d.dispatch(AgentAction(name="finish", args={"summary": "done"}))
    assert r.ok and r.output == "done"
