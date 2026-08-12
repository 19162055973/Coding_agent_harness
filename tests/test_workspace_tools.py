from pathlib import Path

import pytest

from forgeloop.tools.fs_tools import list_dir, read_file, write_file
from forgeloop.tools.workspace import WorkspaceError, WorkspaceGate


def test_workspace_read_write(tmp_path: Path):
    gate = WorkspaceGate(tmp_path)
    assert write_file(gate, "a.txt", "hello").ok
    r = read_file(gate, "a.txt")
    assert r.ok and r.output == "hello"
    listing = list_dir(gate, ".")
    assert "a.txt" in listing.output


def test_workspace_escape_denied(tmp_path: Path):
    gate = WorkspaceGate(tmp_path)
    with pytest.raises(WorkspaceError):
        gate.resolve("../outside.txt")
    bad = write_file(gate, "../outside.txt", "nope")
    assert not bad.ok
