from forgeloop.guardrails.policy import GuardrailPolicy
from forgeloop.models import AgentAction


def test_deny_rm_rf():
    p = GuardrailPolicy()
    d = p.evaluate(AgentAction(name="run_shell", args={"command": "rm -rf /"}))
    assert d.verdict == "deny"


def test_allow_pytest():
    p = GuardrailPolicy()
    d = p.evaluate(AgentAction(name="run_shell", args={"command": "python -m pytest -q"}))
    assert d.verdict == "allow"


def test_approval_git_push():
    p = GuardrailPolicy(hitl_enabled=True)
    d = p.evaluate(AgentAction(name="run_shell", args={"command": "git push origin main"}))
    assert d.verdict == "needs_approval"


def test_unknown_tool_denied():
    p = GuardrailPolicy()
    d = p.evaluate(AgentAction(name="drop_database", args={}))
    assert d.verdict == "deny"
