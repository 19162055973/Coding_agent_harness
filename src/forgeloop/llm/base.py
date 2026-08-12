from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from forgeloop.models import AgentAction


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    action: AgentAction | None = None


class LLMError(Exception):
    pass


class LLMPort(ABC):
    """Injectable LLM abstraction — real provider or mock."""

    @abstractmethod
    def complete(self, messages: list[LLMMessage], tools_desc: str = "") -> LLMResponse:
        raise NotImplementedError


def parse_action_json(text: str) -> AgentAction:
    """Parse a JSON object with keys name/args from model output."""
    import json
    import re

    text = text.strip()
    # fenced block
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"cannot parse action JSON: {exc}") from exc
    if not isinstance(data, dict) or "name" not in data:
        raise LLMError("action JSON must be an object with 'name'")
    args = data.get("args") or {}
    if not isinstance(args, dict):
        raise LLMError("args must be an object")
    return AgentAction(name=str(data["name"]), args=args, raw=text)
