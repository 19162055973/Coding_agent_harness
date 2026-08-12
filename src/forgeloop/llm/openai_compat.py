from __future__ import annotations

import os
from typing import Any

import httpx

from forgeloop.llm.base import LLMError, LLMMessage, LLMPort, LLMResponse, parse_action_json


class OpenAICompatLLM(LLMPort):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, messages: list[LLMMessage], tools_desc: str = "") -> LLMResponse:
        system_extra = ""
        if tools_desc:
            system_extra = (
                "You are a coding agent. Reply with a single JSON object only: "
                '{"name": "<tool>", "args": {...}}. Available tools:\n' + tools_desc
            )
        payload_msgs: list[dict[str, Any]] = []
        if system_extra:
            payload_msgs.append({"role": "system", "content": system_extra})
        for m in messages:
            payload_msgs.append({"role": m.role, "content": m.content})

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": payload_msgs, "temperature": 0},
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise LLMError(str(exc)) from exc

        try:
            action = parse_action_json(content)
        except LLMError:
            action = None
        return LLMResponse(content=content, action=action)


def build_llm_from_env(api_key: str | None = None) -> LLMPort:
    from forgeloop.llm.mock import MockLLM

    if os.getenv("FORGELOOP_USE_MOCK", "").lower() in {"1", "true", "yes"}:
        return MockLLM()
    key = api_key or os.getenv("FORGELOOP_API_KEY") or ""
    if not key:
        raise LLMError("no API key configured")
    return OpenAICompatLLM(
        api_key=key,
        model=os.getenv("FORGELOOP_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("FORGELOOP_API_BASE", "https://api.openai.com/v1"),
    )
