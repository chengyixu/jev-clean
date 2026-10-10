"""Owner-native execution is explicit, verified and cannot execute plan commands."""

from dataclasses import replace

import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer

from jev_clean.application import service
from jev_clean.infrastructure import owner_execution, owner_tools
from jev_clean.infrastructure.scanner import candidate_from_stat


def test_plan_command_or_owner_path_cannot_be_executed(tmp_path, monkeypatch, neural_boundary):
    assert callable(getattr(service, "execute_selection", None))
    path = tmp_path / "data"
    path.mkdir()
    item = replace(
        candidate_from_stat(path, path.stat(), tmp_path, set()),
        unit="directory",
        operation="owner_prune",
        owner_tool="rm",
        decision=answer("remove"),
        eligible=True,
        recommended=True,
    )
    monkeypatch.setattr(owner_tools, "owner_observations", lambda: [])
    result = service.execute_selection([item], home=tmp_path)
    assert result.completed == 0 and result.failed
    assert path.exists()


def test_owner_executor_uses_reobserved_fixed_argv_and_records_irreversibility(tmp_path, monkeypatch):
    assert callable(getattr(owner_execution, "prune_selected", None))
    path = tmp_path / "cache"
    path.mkdir()
    item = replace(
        candidate_from_stat(path, path.stat(), tmp_path, set()),
        unit="directory",
        operation="owner_prune",
        owner_tool="uv",
        decision=answer("remove"),
        eligible=True,
        recommended=True,
    )
    observation = {
        "owner": "uv",
        "path": str(path),
        "argv": ["/installed/uv", "cache", "prune"],
        "operation": "owner_prune",
        "active": False,
        "state": "Observed verified owner-native action",
    }
    monkeypatch.setattr(owner_tools, "owner_observations", lambda: [observation])
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        from subprocess import CompletedProcess

        return CompletedProcess(argv, 0, stdout="Removed 3 files", stderr="")

    result = owner_execution.prune_selected(item, runner=runner)
    assert calls == [["/installed/uv", "cache", "prune"]]
    assert result["reversible"] is False and result["complete"] is True
    assert path.exists()


def test_current_active_owner_refuses_execution_not_merely_scan(tmp_path, monkeypatch):
    assert callable(getattr(owner_execution, "prune_selected", None))
    path = tmp_path / "cache"
    path.mkdir()
    item = replace(
        candidate_from_stat(path, path.stat(), tmp_path, set()),
        unit="directory",
        operation="owner_prune",
        owner_tool="pnpm",
    )
    monkeypatch.setattr(
        owner_tools,
        "owner_observations",
        lambda: [{"owner": "pnpm", "path": str(path), "active": True, "argv": ["/pnpm", "store", "prune"]}],
    )
    with pytest.raises(ValueError, match="active"):
        owner_execution.prune_selected(item, runner=lambda *args, **kw: pytest.fail("must not run"))


def test_owner_confirmation_never_claims_trash_or_undo():
    from jev_clean.ui.screens import ConfirmScreen

    item = replace(candidate(), unit="directory", operation="owner_prune", owner_tool="pnpm")
    screen = ConfirmScreen([item])
    assert "prune" in screen.detail.lower()
    assert "cannot be undone" in screen.detail.lower()
    assert "recoverable" not in screen.detail.lower()
