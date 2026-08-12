from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    WAITING_HITL = "waiting_hitl"
    STEP_LIMIT = "step_limit"


@dataclass
class AgentAction:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    raw: str | None = None


@dataclass
class ToolResult:
    ok: bool
    output: str = ""
    error: str = ""

    def as_observation(self) -> str:
        if self.ok:
            return self.output or "(ok)"
        return f"ERROR: {self.error or self.output}"


@dataclass
class GuardDecision:
    verdict: str  # allow | deny | needs_approval
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.verdict == "allow"


@dataclass
class TestFailure:
    __test__ = False
    nodeid: str
    message: str
    classification: str = "unknown"


@dataclass
class TestReport:
    passed: bool
    total: int = 0
    failed: int = 0
    failures: list[TestFailure] = field(default_factory=list)
    raw: str = ""


@dataclass
class FeedbackEvent:
    kind: str
    classification: str
    summary: str
    raw_ref: str = ""


@dataclass
class AgentStep:
    index: int
    action: AgentAction
    guard: GuardDecision
    result: ToolResult | None = None
    feedback: FeedbackEvent | None = None
    observation: str = ""


@dataclass
class AgentTask:
    id: str
    goal: str
    workspace: str
    max_steps: int = 20
    session_id: str | None = None


@dataclass
class AgentRunResult:
    status: RunStatus
    steps: list[AgentStep] = field(default_factory=list)
    final_message: str = ""
    pending_action: AgentAction | None = None
