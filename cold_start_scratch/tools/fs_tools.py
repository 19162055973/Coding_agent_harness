"""Task 2 scratch — file tools (SPEC §3.3 table).

PAUSE P11/P12: return shapes and list_dir semantics underspecified.
Returns provisional dicts — NOT claimed to match production ToolResult.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .workspace import WorkspaceEscapeError, WorkspaceGate


def read_file(gate: WorkspaceGate, relative_path: str) -> dict[str, Any]:
    """SPEC: read_file | relative path | read workspace file | content or error."""
    try:
        path = gate.resolve(relative_path)
        if not path.is_file():
            return {"ok": False, "error": f"not a file: {relative_path}", "_provisional": True}
        return {"ok": True, "output": path.read_text(encoding="utf-8"), "_provisional": True}
    except (WorkspaceEscapeError, OSError) as exc:
        return {"ok": False, "error": str(exc), "_provisional": True}


def write_file(gate: WorkspaceGate, relative_path: str, content: str) -> dict[str, Any]:
    """SPEC: write_file | relative path + content | write (no escape) | ok / error."""
    try:
        path = gate.resolve(relative_path)
        # PAUSE: parent mkdir behavior not specified — STOP if parents missing?
        # Provisional: create parents so write is usable in tests; FLAG as guess.
        path.parent.mkdir(parents=True, exist_ok=True)  # GUESS — see REPORT Q
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "output": "ok", "_provisional": True}
    except (WorkspaceEscapeError, OSError) as exc:
        return {"ok": False, "error": str(exc), "_provisional": True}


def list_dir(gate: WorkspaceGate, relative_path: str = ".") -> dict[str, Any]:
    """SPEC: list_dir | relative path | list directory | entry list.

    PAUSE P12: names only, non-recursive — provisional interpretation.
    """
    try:
        path = gate.resolve(relative_path)
        if not path.is_dir():
            return {"ok": False, "error": f"not a directory: {relative_path}", "_provisional": True}
        entries = sorted(p.name for p in path.iterdir())
        return {"ok": True, "output": entries, "_provisional": True}
    except (WorkspaceEscapeError, OSError) as exc:
        return {"ok": False, "error": str(exc), "_provisional": True}
