"""One jev-clean run per user owns the model. A second run fails before it loads another model copy.

Before, the lock lived in DecisionCache, after model load, system-wide lsof and the native probes,
so an agent `status --json` started during a TUI scan loaded a second ~2.5 GB model first.
"""

import fcntl
import os

import pytest

from jev_clean import cli
from jev_clean.infrastructure import model


@pytest.fixture
def held(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    loads = []
    monkeypatch.setattr(model.LayaAdvisor, "load", lambda self: loads.append(1))
    state = tmp_path / ".local/state/jev-clean"
    state.mkdir(parents=True, mode=0o700)
    fd = os.open(state / "run.lock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    yield loads
    os.close(fd)


@pytest.mark.parametrize(
    "argv",
    [["status", "--json"], ["clean", "--json"], ["status", "--json", "--demo"], ["doctor", "--verify-model"]],
)
def test_second_run_fails_before_loading_the_model(held, argv, capsys):
    assert cli.main(argv) == 1
    assert held == []
    assert "Another jev-clean run is active" in capsys.readouterr().err


def test_apply_fails_before_reading_the_plan(held, tmp_path, capsys):
    assert cli.main(["apply", str(tmp_path / "missing.json"), "--ids", "x"]) == 1
    assert "Another jev-clean run is active" in capsys.readouterr().err


def test_read_only_commands_do_not_need_the_run_lock(held, capsys):
    assert cli.main(["history"]) == 0
    assert cli.main(["completion", "zsh"]) == 0
