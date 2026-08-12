from __future__ import annotations

from forgeloop.feedback.sensor import TestSensor
from forgeloop.models import AgentAction, ToolResult
from forgeloop.tools import fs_tools
from forgeloop.tools.shell_tool import run_shell
from forgeloop.tools.workspace import WorkspaceGate


TOOLS_DESC = """
- read_file: args.path
- write_file: args.path, args.content
- list_dir: args.path (optional)
- run_shell: args.command
- run_tests: args.extra (optional pytest args)
- finish: args.summary
""".strip()


class ToolDispatcher:
    def __init__(self, gate: WorkspaceGate, test_command: str = "python -m pytest -q"):
        self.gate = gate
        self.sensor = TestSensor(workspace=gate.root, command=test_command)

    def dispatch(self, action: AgentAction) -> ToolResult:
        name = action.name
        args = action.args or {}
        if name == "read_file":
            return fs_tools.read_file(self.gate, str(args.get("path", "")))
        if name == "write_file":
            return fs_tools.write_file(
                self.gate, str(args.get("path", "")), str(args.get("content", ""))
            )
        if name == "list_dir":
            return fs_tools.list_dir(self.gate, str(args.get("path", ".")))
        if name == "run_shell":
            return run_shell(self.gate.root, str(args.get("command", "")))
        if name == "run_tests":
            extra = str(args.get("extra", "")).strip()
            report = self.sensor.run(extra=extra)
            summary = (
                f"passed={report.passed} total={report.total} failed={report.failed}\n"
                + report.raw
            )
            return ToolResult(ok=report.passed, output=summary, error="" if report.passed else "tests failed")
        if name == "finish":
            return ToolResult(ok=True, output=str(args.get("summary", "done")))
        return ToolResult(ok=False, error=f"unknown tool: {name}")
