"""Regressions for classification vetoes masquerading as model judgments."""

from dataclasses import replace

import pytest
from test_contracts import candidate

from jev_clean.domain.models import Decision
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.scanner import candidate_from_stat
from jev_clean.infrastructure.trash import TrashStore


def answer(choice):
    return Decision(
        choice,
        {k: 1.0 if k == choice else 0.0 for k in ("keep", "review", "remove")},
        "test neural boundary",
        1,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "database"},
        {"kind": "protected"},
        {"age_seconds": 0},
        {"open_file": True},
        {"open_file": None},
        {"fingerprint": replace(candidate().fingerprint, nlink=2)},
    ],
)
def test_facts_do_not_override_model_classification(changes):
    item = candidate(**changes)
    result = apply_policy(item, answer("remove"))
    assert result.recommended and result.selectable
    for label in ("keep", "review"):
        result = apply_policy(item, answer(label))
        assert result.decision.choice == label
        assert not result.recommended and not result.selectable


def test_execution_inability_does_not_rewrite_model_recommendation():
    result = apply_policy(candidate(scan_complete=False), answer("remove"))
    assert result.recommended
    assert not result.eligible and not result.selectable
    assert result.decision.choice == "remove"


def test_new_database_outside_old_roots_can_be_staged_and_restored(tmp_path):
    # Synthetic data ONLY. Proves extension, age and old-root vetoes are gone end-to-end.
    home = tmp_path / "home"
    home.mkdir()
    path = tmp_path / "project/generated.sqlite"
    path.parent.mkdir()
    path.write_bytes(b"synthetic disposable database")
    item = candidate_from_stat(path, path.stat(), home, set())
    item = apply_policy(item, answer("remove"))
    store = TrashStore(home)
    result = store.move([item], open_paths=set())
    assert result.moved == 1, result.failed
    assert not path.exists()
    restored = store.restore(result.batch_id)
    assert restored.moved == 1, restored.failed
    assert path.read_bytes() == b"synthetic disposable database"


def test_execution_refuses_forged_remove_boolean_with_keep_decision(tmp_path):
    path = tmp_path / "keep"
    path.write_bytes(b"keep")
    item = candidate_from_stat(path, path.stat(), tmp_path, set())
    item = replace(item, eligible=True, recommended=True, decision=answer("keep"))
    result = TrashStore(tmp_path).move([item], open_paths=set())
    assert result.moved == 0 and path.read_bytes() == b"keep"
