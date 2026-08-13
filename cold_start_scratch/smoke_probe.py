"""Minimal smoke probes — not full pytest suite (acceptance criteria absent from PLAN)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cold_start_scratch.tools import WorkspaceGate, list_dir, read_file, write_file
from cold_start_scratch.llm import MockLLM, LLMResponse


def probe_workspace_escape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        gate = WorkspaceGate(tmp)
        try:
            gate.resolve("../outside.txt")
            raise AssertionError("expected escape to fail")
        except Exception as exc:
            print("escape blocked:", type(exc).__name__, exc)


def probe_rw() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        gate = WorkspaceGate(tmp)
        w = write_file(gate, "a.txt", "hello")
        assert w.get("ok"), w
        r = read_file(gate, "a.txt")
        assert r.get("output") == "hello", r
        listing = list_dir(gate, ".")
        assert "a.txt" in listing.get("output", []), listing
        print("rw+list ok (provisional ToolResult dict)")


def probe_llm_response_blocked() -> None:
    try:
        LLMResponse(content="x")
    except NotImplementedError as exc:
        print("LLMResponse correctly blocked:", exc)


def probe_mock_queue() -> None:
    mock = MockLLM(script=[{"probe": True}, "text-action"])
    assert mock.complete([], None) == {"probe": True}
    assert mock.complete([], None) == "text-action"
    try:
        mock.complete([], None)
    except NotImplementedError as exc:
        print("empty queue blocked:", exc)


if __name__ == "__main__":
    # Allow running as script if package root is on PYTHONPATH
    probe_workspace_escape()
    probe_rw()
    probe_llm_response_blocked()
    probe_mock_queue()
    print("smoke probes finished — see REPORT.md for non-guessed gaps")
