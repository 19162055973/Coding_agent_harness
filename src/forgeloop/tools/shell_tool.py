from __future__ import annotations

import subprocess
from pathlib import Path

from forgeloop.models import ToolResult


def run_shell(
    cwd: str | Path,
    command: str,
    timeout: float = 60.0,
) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(ok=False, error="empty command")
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, error=f"timeout after {timeout}s")
    except OSError as exc:
        return ToolResult(ok=False, error=str(exc))

    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    if proc.returncode != 0:
        return ToolResult(ok=False, output=out.strip(), error=f"exit {proc.returncode}")
    return ToolResult(ok=True, output=out.strip())
