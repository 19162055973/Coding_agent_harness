"""Task 1 scratch — LLMPort / MockLLM (SPEC §3.2 only).

PAUSE: Many contracts are underspecified in SPEC+PLAN.
This module intentionally does NOT invent a complete API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Iterator, Optional


class LLMError(Exception):
    """SPEC §3.2: HTTP/auth errors wrap as LLMError.

    PAUSE P6: no required fields (status_code, message, cause) specified.
    """


class LLMResponse:
    """SPEC §6 names LLMResponse but does not define fields.

    PAUSE P2: STOP — do not invent `content` / `action` / `raw` without human confirmation.
    Placeholder only so import paths exist for cold-start proof.
    """

    def __init__(self, **kwargs: Any) -> None:
        # Intentionally refuse to normalize unknown kwargs into a schema.
        raise NotImplementedError(
            "PAUSE P2: LLMResponse fields are not defined in SPEC.md §6. "
            "Ask human before implementing."
        )


class LLMPort(ABC):
    """SPEC §3.2: LLMPort.complete(...) returns structured action or text."""

    @abstractmethod
    def complete(self, messages: Any, tool_schema: Any) -> Any:
        """PAUSE P3: message/tool_schema/return types unspecified.

        SPEC wording: input = messages + tool schema; output = LLMResponse.
        Also: '返回结构化动作或文本' (PAUSE P5 — union vs single type?).
        """
        raise NotImplementedError


class MockLLM(LLMPort):
    """SPEC §3.2: MockLLM emits predetermined actions from a script queue.

    PAUSE P4: queue element type and empty-queue behavior unspecified.
    """

    def __init__(self, script: Optional[Iterable[Any]] = None) -> None:
        # Accept opaque objects only — cannot validate against unknown schema.
        self._queue: Iterator[Any] = iter(list(script or []))

    def complete(self, messages: Any, tool_schema: Any) -> Any:
        # PAUSE P4/P5: cannot construct LLMResponse / AgentAction safely.
        try:
            item = next(self._queue)
        except StopIteration as exc:
            raise NotImplementedError(
                "PAUSE P4: exhausted MockLLM queue behavior not specified "
                "(error vs finish vs empty text)."
            ) from exc
        # Returning raw script item is a temporary probe, NOT a SPEC-compliant contract.
        return item


# --- Attempted AgentAction (shared model) ------------------------------------

def agent_action_sketch() -> None:
    """SPEC §6: AgentAction: type/name, args, raw

    PAUSE P7: 'type/name' could mean:
      (a) one field that is either type or name,
      (b) two fields type and name,
      (c) field named type with tool name value.
    STOP — do not implement dataclass.
    """
    raise NotImplementedError("PAUSE P7: AgentAction field naming ambiguous")
