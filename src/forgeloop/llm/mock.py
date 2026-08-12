from __future__ import annotations

from forgeloop.llm.base import LLMMessage, LLMPort, LLMResponse, LLMError, parse_action_json
from forgeloop.models import AgentAction


class MockLLM(LLMPort):
    """Scripted LLM for deterministic offline tests."""

    def __init__(self, script: list[AgentAction | str] | None = None):
        self._script: list[AgentAction | str] = list(script or [])
        self.calls: list[list[LLMMessage]] = []

    def push(self, item: AgentAction | str) -> None:
        self._script.append(item)

    def complete(self, messages: list[LLMMessage], tools_desc: str = "") -> LLMResponse:
        self.calls.append(list(messages))
        if not self._script:
            raise LLMError("MockLLM script exhausted")
        item = self._script.pop(0)
        if isinstance(item, AgentAction):
            return LLMResponse(content=item.raw or item.name, action=item)
        action = parse_action_json(item)
        return LLMResponse(content=item, action=action)
