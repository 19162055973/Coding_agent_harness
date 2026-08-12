from __future__ import annotations

from forgeloop.models import ToolResult
from forgeloop.tools.workspace import WorkspaceError, WorkspaceGate


def read_file(gate: WorkspaceGate, path: str) -> ToolResult:
    try:
        return ToolResult(ok=True, output=gate.read_text(path))
    except WorkspaceError as exc:
        return ToolResult(ok=False, error=str(exc))


def write_file(gate: WorkspaceGate, path: str, content: str) -> ToolResult:
    try:
        gate.write_text(path, content)
        return ToolResult(ok=True, output=f"wrote {path}")
    except WorkspaceError as exc:
        return ToolResult(ok=False, error=str(exc))


def list_dir(gate: WorkspaceGate, path: str = ".") -> ToolResult:
    try:
        items = gate.list_dir(path)
        return ToolResult(ok=True, output="\n".join(items) if items else "(empty)")
    except WorkspaceError as exc:
        return ToolResult(ok=False, error=str(exc))
