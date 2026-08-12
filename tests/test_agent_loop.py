from pathlib import Path

from forgeloop.llm.mock import MockLLM
from forgeloop.loop.agent_loop import AgentLoop
from forgeloop.models import AgentAction, AgentTask, RunStatus


def test_loop_write_and_finish(tmp_path: Path):
    llm = MockLLM(
        [
            AgentAction(
                name="write_file",
                args={"path": "x.py", "content": "print(1)\n"},
            ),
            AgentAction(name="finish", args={"summary": "done"}),
        ]
    )
    result = AgentLoop(llm=llm).run(
        AgentTask(id="t1", goal="write x.py", workspace=str(tmp_path), max_steps=5)
    )
    assert result.status == RunStatus.SUCCEEDED
    assert (tmp_path / "x.py").read_text(encoding="utf-8") == "print(1)\n"


def test_loop_guard_denies(tmp_path: Path):
    llm = MockLLM([AgentAction(name="run_shell", args={"command": "rm -rf /"})])
    result = AgentLoop(llm=llm).run(
        AgentTask(id="t2", goal="danger", workspace=str(tmp_path), max_steps=3)
    )
    assert result.status == RunStatus.DENIED


def test_loop_feedback_changes_action(tmp_path: Path):
    llm = MockLLM(
        [
            AgentAction(name="run_tests", args={}),
            AgentAction(
                name="write_file",
                args={"path": "test_ok.py", "content": "def test_ok():\n    assert True\n"},
            ),
            AgentAction(name="finish", args={"summary": "fixed"}),
        ]
    )
    result = AgentLoop(llm=llm).run(
        AgentTask(id="t3", goal="pass tests", workspace=str(tmp_path), max_steps=5)
    )
    assert result.status == RunStatus.SUCCEEDED
    assert result.steps[0].action.name == "run_tests"
    assert result.steps[0].feedback is not None
    assert result.steps[1].action.name == "write_file"
    assert "Feedback" in llm.calls[1][0].content or "tests" in llm.calls[1][0].content.lower()
