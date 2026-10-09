"""Directory staging is explicit, identity-bound and reversible; fixtures only."""

from dataclasses import replace

import pytest
from cache_fixtures import declare_cache
from test_model_owned_judgment import answer

from jev_clean.application import service
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource
from jev_clean.infrastructure.trash import TrashStore


def proposal(home):
    path = home / "cache"
    (path / "nested").mkdir(parents=True)
    (path / "nested/blob").write_bytes(b"resource data")
    declare_cache(path)
    return apply_policy(measure_resource(path, home, EvidenceCollector(home), set()), answer("remove"))


def test_unsealed_directory_cannot_be_moved(tmp_path):
    item = proposal(tmp_path)
    r = TrashStore(tmp_path).move([item], open_paths=set())
    assert r.moved == 0
    assert (tmp_path / "cache/nested/blob").exists()
    assert "manifest" in str(r.failed).lower()


def test_selected_resource_is_sealed_staged_and_restored(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    assert callable(getattr(service, "prepare_selection", None))
    sealed = service.prepare_selection([item], home=tmp_path)
    assert sealed[0].manifest_digest
    assert sealed[0].member_count == 3
    assessed = service.reassess_selection(sealed, home=tmp_path)
    store = TrashStore(tmp_path)
    r = store.move(assessed, open_paths=set())
    assert r.moved == 1, r.failed
    assert not (tmp_path / "cache").exists()
    restored = store.restore(r.batch_id)
    assert restored.moved == 1, restored.failed
    assert (tmp_path / "cache/nested/blob").read_bytes() == b"resource data"


def test_deep_change_after_review_is_refused_even_when_root_did_not_change(
    tmp_path, monkeypatch, neural_boundary
):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    assert callable(getattr(service, "prepare_selection", None))
    sealed = service.prepare_selection([item], home=tmp_path)
    (tmp_path / "cache/nested/blob").write_bytes(b"new valuable work")
    with pytest.raises(ValueError, match="changed"):
        service.reassess_selection(sealed, home=tmp_path)
    r = TrashStore(tmp_path).move(sealed, open_paths=set())
    assert r.moved == 0 and (tmp_path / "cache/nested/blob").exists()


def test_overlapping_selection_is_rejected_before_any_move(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    assert callable(getattr(service, "prepare_selection", None))
    child = replace(item, id="child", path=str(tmp_path / "cache/nested"))
    with pytest.raises(ValueError, match="overlap"):
        service.prepare_selection([item, child], home=tmp_path)
    assert (tmp_path / "cache/nested/blob").exists()
