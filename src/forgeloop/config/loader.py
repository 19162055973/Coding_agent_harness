from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class HarnessConfig:
    max_steps: int = 20
    test_command: str = "python -m pytest -q"
    hitl_enabled: bool = True
    model: str = "gpt-4o-mini"
    deny_patterns: list[str] = field(default_factory=list)
    approval_patterns: list[str] = field(default_factory=list)
    memory_limit: int = 5

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessConfig":
        cfg = cls()
        if not isinstance(data, dict):
            raise ValueError("config root must be a mapping")
        if "max_steps" in data:
            cfg.max_steps = int(data["max_steps"])
            if cfg.max_steps < 1:
                raise ValueError("max_steps must be >= 1")
        if "test_command" in data:
            cfg.test_command = str(data["test_command"])
        if "hitl_enabled" in data:
            cfg.hitl_enabled = bool(data["hitl_enabled"])
        if "model" in data:
            cfg.model = str(data["model"])
        if "deny_patterns" in data:
            cfg.deny_patterns = list(data["deny_patterns"])
        if "approval_patterns" in data:
            cfg.approval_patterns = list(data["approval_patterns"])
        if "memory_limit" in data:
            cfg.memory_limit = int(data["memory_limit"])
        return cfg


def default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "default.yaml"


def load_config(path: str | Path | None = None) -> HarnessConfig:
    p = Path(path) if path else default_config_path()
    if not p.exists():
        return HarnessConfig()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return HarnessConfig.from_dict(data)
