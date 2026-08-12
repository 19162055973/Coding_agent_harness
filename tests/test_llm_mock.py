from forgeloop.llm.base import LLMError, parse_action_json
from forgeloop.llm.mock import MockLLM
from forgeloop.models import AgentAction
import pytest


def test_parse_action_json():
    action = parse_action_json('{"name": "finish", "args": {"summary": "x"}}')
    assert action.name == "finish"
    assert action.args["summary"] == "x"


def test_mock_llm_queue():
    llm = MockLLM([AgentAction(name="list_dir", args={"path": "."})])
    resp = llm.complete([])
    assert resp.action is not None
    assert resp.action.name == "list_dir"
    with pytest.raises(LLMError):
        llm.complete([])
