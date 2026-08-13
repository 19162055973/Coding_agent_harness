"""Task 2 scratch — WorkspaceGate (SPEC §3.3 path rule only)."""

from __future__ import annotations

from pathlib import Path


class WorkspaceEscapeError(ValueError):
    """Raised when a path would leave the workspace root."""


class WorkspaceGate:
    """SPEC §3.3: paths resolved via WorkspaceGate; forbid `..` escape.

    PAUSE P9: method names / absolute-path / symlink policy unspecified.
    Implemented the *minimum behavioral rule* stated in SPEC:
    resolve a relative path under root and reject escapes.
    Method name `resolve` is PROVISIONAL (not in SPEC).
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def resolve(self, relative_path: str) -> Path:
        """PROVISIONAL API name — not mandated by SPEC/PLAN.

        Clear from SPEC: relative paths; no `..` escape past workspace root.
        Unclear (PAUSE P10): absolute inputs, Windows drives, symlink escape.
        """
        # Reject empty / None-like
        if relative_path is None or str(relative_path).strip() == "":
            raise WorkspaceEscapeError("empty path rejected (provisional rule)")

        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceEscapeError(
                f"path escapes workspace: {relative_path!r}"
            ) from exc
        return candidate
