from __future__ import annotations

import re
from dataclasses import dataclass, field

from forgeloop.models import AgentAction, GuardDecision


DEFAULT_DENY_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+/\*",
    r"rm\s+-r\s+/",
    r"del\s+/s\s+/q\s+[a-zA-Z]:\\",
    r"format\s+[a-zA-Z]:",
    r"mkfs\b",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"curl\s+[^\n]*\|\s*(ba)?sh",
    r"wget\s+[^\n]*\|\s*(ba)?sh",
    r">\s*/etc/",
    r"\brm\s+-rf\s+\.\.",
]

DEFAULT_APPROVAL_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bdocker\s+push\b",
    r"\bpip\s+install\b",
]


@dataclass
class GuardrailPolicy:
    deny_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_DENY_PATTERNS))
    approval_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_APPROVAL_PATTERNS))
    hitl_enabled: bool = True
    deny_unknown_tools: bool = True
    known_tools: set[str] = field(
        default_factory=lambda: {
            "read_file",
            "write_file",
            "list_dir",
            "run_shell",
            "run_tests",
            "finish",
        }
    )

    def _match(self, text: str, patterns: list[str]) -> str | None:
        for pat in patterns:
            if re.search(pat, text, flags=re.IGNORECASE):
                return pat
        return None

    def evaluate(self, action: AgentAction) -> GuardDecision:
        name = action.name
        if name not in self.known_tools:
            if self.deny_unknown_tools:
                return GuardDecision(verdict="deny", reason=f"unknown tool: {name}")
            return GuardDecision(verdict="needs_approval", reason=f"unknown tool: {name}")

        if name == "run_shell":
            cmd = str((action.args or {}).get("command", ""))
            hit = self._match(cmd, self.deny_patterns)
            if hit:
                return GuardDecision(verdict="deny", reason=f"dangerous command matched: {hit}")
            if self.hitl_enabled:
                hit = self._match(cmd, self.approval_patterns)
                if hit:
                    return GuardDecision(
                        verdict="needs_approval", reason=f"requires approval: {hit}"
                    )

        if name == "write_file":
            path = str((action.args or {}).get("path", ""))
            if path.startswith("/") or re.match(r"^[a-zA-Z]:\\", path):
                # absolute — WorkspaceGate will also catch; treat as needs care
                if ".." in path or path.startswith("/etc"):
                    return GuardDecision(verdict="deny", reason="suspicious absolute write")

        return GuardDecision(verdict="allow", reason="ok")
