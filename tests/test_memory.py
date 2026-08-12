from pathlib import Path

from forgeloop.memory.store import MemoryStore


def test_memory_search(tmp_path: Path):
    store = MemoryStore(tmp_path / "m.jsonl")
    store.add("s1", "prefer pytest -q", kind="convention")
    store.add("s1", "use black", kind="convention")
    store.add("s2", "other session", kind="note")
    hits = store.search("s1", query="pytest", limit=5)
    assert len(hits) == 1
    assert "pytest" in hits[0].text
    text = store.format_hits(hits)
    assert "Memory:" in text
