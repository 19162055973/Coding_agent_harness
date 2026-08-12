from __future__ import annotations

from pathlib import Path


class WorkspaceError(ValueError):
    pass


class WorkspaceGate:
    """Resolve and enforce paths stay inside workspace root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise WorkspaceError(f"workspace is not a directory: {self.root}")

    def resolve(self, rel: str) -> Path:
        if rel is None or str(rel).strip() == "":
            raise WorkspaceError("path is empty")
        # reject absolute paths that are outside
        candidate = Path(rel)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(f"path escapes workspace: {rel}") from exc
        return resolved

    def read_text(self, rel: str, max_bytes: int = 200_000) -> str:
        path = self.resolve(rel)
        if not path.is_file():
            raise WorkspaceError(f"not a file: {rel}")
        data = path.read_bytes()
        if len(data) > max_bytes:
            raise WorkspaceError(f"file too large: {rel}")
        return data.decode("utf-8", errors="replace")

    def write_text(self, rel: str, content: str) -> None:
        path = self.resolve(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_dir(self, rel: str = ".") -> list[str]:
        path = self.resolve(rel)
        if not path.is_dir():
            raise WorkspaceError(f"not a directory: {rel}")
        return sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
