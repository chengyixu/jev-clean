"""Irreversible owner operations require CLEAN, cannot masquerade as Trash moves."""

from dataclasses import replace

from test_contracts import candidate
from test_model_owned_judgment import answer

from jev_clean import cli
from jev_clean.domain.models import CleanupResult
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.trash import TrashStore


def test_cli_owner_prune_rejects_trash_confirmation_before_execution(tmp_path, monkeypatch, capsys):
    item = apply_policy(replace(candidate(), operation="owner_prune", owner_tool="uv"), answer("remove"))
    monkeypatch.setattr(cli, "load_plan", lambda *a: [item])
    monkeypatch.setattr(
        cli, "execute_selection", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not execute"))
    )
    assert cli.main(["apply", str(tmp_path / "plan.json"), "--ids", item.id, "--confirm", "TRASH"]) == 1
    assert "CLEAN" in capsys.readouterr().err


def test_cli_owner_prune_explicit_clean_runs_only_selected_id(tmp_path, monkeypatch, capsys):
    item = apply_policy(replace(candidate(), operation="owner_prune", owner_tool="pnpm"), answer("remove"))
    monkeypatch.setattr(cli, "load_plan", lambda *a: [item])
    seen = []
    monkeypatch.setattr(
        cli,
        "execute_selection",
        lambda items, **kw: seen.extend(items) or CleanupResult(completed=1, pruned=1),
    )
    assert cli.main(["apply", str(tmp_path / "plan.json"), "--ids", item.id, "--confirm", "CLEAN"]) == 0
    assert [i.id for i in seen] == [item.id]
    assert '"pruned": 1' in capsys.readouterr().out


def test_trash_executor_never_runs_owner_operation(tmp_path):
    path = tmp_path / "cache"
    path.mkdir()
    from jev_clean.infrastructure.scanner import candidate_from_stat

    item = apply_policy(
        replace(
            candidate_from_stat(path, path.stat(), tmp_path, set()),
            unit="directory",
            operation="owner_prune",
            owner_tool="uv",
            execution_issue="",
        ),
        answer("remove"),
    )
    r = TrashStore(tmp_path).move([item], open_paths=set())
    assert r.moved == 0 and path.exists()
    assert "Owner-native" in str(r.failed)
