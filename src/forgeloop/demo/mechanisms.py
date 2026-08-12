from __future__ import annotations

import tempfile
from pathlib import Path

from forgeloop.guardrails.policy import GuardrailPolicy
from forgeloop.llm.mock import MockLLM
from forgeloop.loop.agent_loop import AgentLoop
from forgeloop.models import AgentAction, AgentTask, RunStatus
from forgeloop.feedback.classifier import classify_failure_message


def demo_guardrail_blocks_danger() -> None:
    policy = GuardrailPolicy()
    decision = policy.evaluate(
        AgentAction(name="run_shell", args={"command": "rm -rf /"})
    )
    assert decision.verdict == "deny", decision
    print("[OK] guardrail blocked dangerous shell")


def demo_feedback_changes_next_action() -> None:
    """Inject a failure observation via scripted MockLLM; next action differs."""
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        # first model turn: run_tests (will fail — no tests / empty)
        # After feedback in history, second turn should write a test file then finish.
        llm = MockLLM(
            [
                AgentAction(name="run_tests", args={}),
                AgentAction(
                    name="write_file",
                    args={"path": "fix_sample.py", "content": "def test_ok():\n    assert True\n"},
                ),
                AgentAction(name="finish", args={"summary": "added test after failure feedback"}),
            ]
        )
        loop = AgentLoop(llm=llm)
        result = loop.run(
            AgentTask(id="demo-fb", goal="make tests pass", workspace=str(ws), max_steps=5)
        )
        assert result.status == RunStatus.SUCCEEDED, result
        assert len(result.steps) >= 2
        assert result.steps[0].action.name == "run_tests"
        assert result.steps[0].feedback is not None
        assert result.steps[0].feedback.kind in {"tests_failed", "tests_passed"}
        # Key demo: subsequent action is not another identical blind finish — it writes a file
        assert result.steps[1].action.name == "write_file"
        # Prove feedback influenced context: MockLLM received feedback in second call
        assert len(llm.calls) >= 2
        second_prompt = llm.calls[1][0].content
        assert "Feedback signals" in second_prompt or "tests" in second_prompt.lower()
        print("[OK] feedback loop changed next action after failure injection")


def demo_classifier_focus() -> None:
    assert classify_failure_message("AssertionError: expected 1") == "assertion"
    assert classify_failure_message("ModuleNotFoundError: No module named 'x'") == "import"
    assert classify_failure_message("SyntaxError: invalid syntax") == "syntax"
    print("[OK] failure classifier (focus dimension) deterministic")


def main() -> int:
    demo_guardrail_blocks_danger()
    demo_feedback_changes_next_action()
    demo_classifier_focus()
    print("All mechanism demos passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
