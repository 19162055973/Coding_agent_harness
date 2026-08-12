from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class MemoryEntry:
    id: str
    session_id: str
    kind: str
    text: str
    created_at: float


class MemoryStore:
    """Simple JSONL memory — self-implemented, no framework memory."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def add(self, session_id: str, text: str, kind: str = "note") -> MemoryEntry:
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            session_id=session_id,
            kind=kind,
            text=text,
            created_at=time.time(),
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def _load(self) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return entries
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(MemoryEntry(**data))
            except (json.JSONDecodeError, TypeError):
                continue
        return entries

    def search(
        self, session_id: str, query: str = "", limit: int = 5, project_scope: bool = False
    ) -> list[MemoryEntry]:
        q = (query or "").lower()
        items = self._load()
        if not project_scope:
            items = [e for e in items if e.session_id == session_id]
        if q:
            items = [e for e in items if q in e.text.lower() or q in e.kind.lower()]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[:limit]

    def format_hits(self, hits: list[MemoryEntry]) -> str:
        if not hits:
            return ""
        lines = [f"- ({h.kind}) {h.text}" for h in hits]
        return "Memory:\n" + "\n".join(lines)
