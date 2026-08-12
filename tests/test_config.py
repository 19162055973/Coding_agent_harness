from pathlib import Path

import pytest

from forgeloop.config.loader import HarnessConfig, load_config


def test_default_config():
    cfg = load_config(Path("nonexistent-forgeloop.yaml"))
    assert cfg.max_steps >= 1


def test_config_validation(tmp_path: Path):
    p = tmp_path / "c.yaml"
    p.write_text("max_steps: 0\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(p)


def test_config_ok(tmp_path: Path):
    p = tmp_path / "c.yaml"
    p.write_text("max_steps: 3\ntest_command: 'pytest -q'\n", encoding="utf-8")
    cfg = load_config(p)
    assert cfg.max_steps == 3
