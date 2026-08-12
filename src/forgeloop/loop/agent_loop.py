from __future__ import annotations

from forgeloop.config.loader import HarnessConfig
from forgeloop.feedback.sensor import TestSensor
from forgeloop.guardrails.policy import GuardrailPolicy
from forgeloop.llm.base import LLMError, LLMMessage, LLMPort
from forgeloop.memory.store import MemoryStore
from forgeloop.models import (
    AgentAction,
    AgentRunResult,
    AgentStep,
    AgentTask,
    GuardDecision,
    RunStatus,
    ToolResult,
)
from forgeloop.tools.dispatcher import TOOLS_DESC, ToolDispatcher
from forgeloop.tools.workspace import WorkspaceGate


class AgentLoop:
    """Harness kernel: context → LLM → guard → tool → feedback → stop."""

    def __init__(
        self,
        llm: LLMPort,
        config: HarnessConfig | None = None,
        memory: MemoryStore | None = None,
        policy: GuardrailPolicy | None = None,
    ):
        self.llm = llm
        self.config = config or HarnessConfig()
        self.memory = memory
        self.policy = policy or GuardrailPolicy(hitl_enabled=self.config.hitl_enabled)
        if self.config.deny_patterns:
            self.policy.deny_patterns = list(self.config.deny_patterns) + self.policy.deny_patterns
        if self.config.approval_patterns:
            self.policy.approval_patterns = (
                list(self.config.approval_patterns) + self.policy.approval_patterns
            )

    def _build_messages(
        self, task: AgentTask, history: list[str], feedback_notes: list[str]
    ) -> list[LLMMessage]:
        parts = [
            f"Goal: {task.goal}",
            f"Workspace: {task.workspace}",
            "Respond with one JSON action per turn.",
        ]
        if self.memory and task.session_id:
            hits = self.memory.search(
                task.session_id, query=task.goal[:40], limit=self.config.memory_limit
            )
            mem = self.memory.format_hits(hits)
            if mem:
                parts.append(mem)
        if feedback_notes:
            parts.append("Feedback signals:\n" + "\n".join(feedback_notes[-5:]))
        if history:
            parts.append("History:\n" + "\n".join(history[-12:]))
        return [LLMMessage(role="user", content="\n\n".join(parts))]

    def run(
        self,
        task: AgentTask,
        resume_approval: bool | None = None,
        pending_action: AgentAction | None = None,
    ) -> AgentRunResult:
        gate = WorkspaceGate(task.workspace)
        dispatcher = ToolDispatcher(gate, test_command=self.config.test_command)
        sensor = TestSensor(gate.root, command=self.config.test_command)

        steps: list[AgentStep] = []
        history: list[str] = []
        feedback_notes: list[str] = []
        max_steps = min(task.max_steps, self.config.max_steps)

        # HITL resume path
        if resume_approval is not None and pending_action is not None:
            if resume_approval is False:
                return AgentRunResult(
                    status=RunStatus.DENIED,
                    steps=steps,
                    final_message="user denied action",
                    pending_action=pending_action,
                )
            fb = None
            if pending_action.name == "run_tests":
                report = sensor.run()
                fb = sensor.to_feedback(report)
                feedback_notes.append(fb.summary)
                result = ToolResult(
                    ok=report.passed,
                    output=fb.summary + "\n" + report.raw[:800],
                    error="" if report.passed else "tests failed",
                )
                obs = result.output
            else:
                result = dispatcher.dispatch(pending_action)
                obs = result.as_observation()
            history.append(f"action={pending_action.name} obs={obs[:500]}")
            step = AgentStep(
                index=0,
                action=pending_action,
                guard=GuardDecision(verdict="allow", reason="approved"),
                result=result,
                feedback=fb,
                observation=obs,
            )
            steps.append(step)
            if pending_action.name == "finish" and result.ok:
                return AgentRunResult(
                    status=RunStatus.SUCCEEDED, steps=steps, final_message=result.output
                )

        for i in range(len(steps), max_steps):
            messages = self._build_messages(task, history, feedback_notes)
            try:
                resp = self.llm.complete(messages, tools_desc=TOOLS_DESC)
            except LLMError as exc:
                return AgentRunResult(
                    status=RunStatus.FAILED, steps=steps, final_message=str(exc)
                )

            action = resp.action
            if action is None:
                # one repair opportunity via observation injection
                history.append(f"invalid_llm_output={resp.content[:300]}")
                feedback_notes.append(
                    "Your last output was not valid JSON action. "
                    'Reply with {"name":..., "args":{...}} only.'
                )
                continue

            guard = self.policy.evaluate(action)
            if guard.verdict == "deny":
                steps.append(
                    AgentStep(
                        index=i,
                        action=action,
                        guard=guard,
                        result=ToolResult(ok=False, error=guard.reason),
                        observation=guard.reason,
                    )
                )
                return AgentRunResult(
                    status=RunStatus.DENIED,
                    steps=steps,
                    final_message=guard.reason,
                    pending_action=action,
                )
            if guard.verdict == "needs_approval":
                steps.append(
                    AgentStep(index=i, action=action, guard=guard, observation=guard.reason)
                )
                return AgentRunResult(
                    status=RunStatus.WAITING_HITL,
                    steps=steps,
                    final_message=guard.reason,
                    pending_action=action,
                )

            fb = None
            if action.name == "run_tests":
                # Feedback path uses TestSensor once (deterministic, no prompt-only check)
                report = sensor.run(extra=str(action.args.get("extra", "")).strip())
                fb = sensor.to_feedback(report)
                feedback_notes.append(fb.summary)
                result = ToolResult(
                    ok=report.passed,
                    output=fb.summary + "\n" + report.raw[:800],
                    error="" if report.passed else "tests failed",
                )
                obs = result.output
            else:
                result = dispatcher.dispatch(action)
                obs = result.as_observation()
                if action.name == "write_file" and not result.ok:
                    feedback_notes.append(f"write failed: {result.error}")

            history.append(f"action={action.name} args={action.args} obs={obs[:500]}")
            steps.append(
                AgentStep(
                    index=i,
                    action=action,
                    guard=guard,
                    result=result,
                    feedback=fb,
                    observation=obs,
                )
            )

            if self.memory and task.session_id and action.name in {"finish", "write_file"}:
                self.memory.add(
                    task.session_id,
                    text=f"{action.name}: {obs[:200]}",
                    kind="decision",
                )

            if action.name == "finish":
                return AgentRunResult(
                    status=RunStatus.SUCCEEDED,
                    steps=steps,
                    final_message=result.output or "done",
                )

        return AgentRunResult(
            status=RunStatus.STEP_LIMIT,
            steps=steps,
            final_message="max steps reached",
        )
