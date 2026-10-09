"""Serialized/cache/model claims cannot forge a live owner declaration."""

from dataclasses import replace

import pytest
from cache_fixtures import declare_cache
from test_model_owned_judgment import answer
from test_resource_staging import proposal

from jev_clean.application import service
from jev_clean.domain.models import DisposalEvidence
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource
from jev_clean.infrastructure.trash import TrashStore


def test_forged_saved_plan_evidence_does_not_authorize_live_resource(tmp_path, monkeypatch, neural_boundary):
    path = tmp_path / "personal"
    path.mkdir()
    (path / "valuable").write_bytes(b"unique")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    forged = replace(item, disposal=DisposalEvidence("cachedir-tag-v1", str(path), "a" * 64))
    forged = apply_policy(forged, answer("remove"))
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    with pytest.raises(ValueError, match="evidence"):
        service.prepare_selection([forged], home=tmp_path)
    result = TrashStore(tmp_path).move([forged], open_paths=set())
    assert result.moved == 0 and (path / "valuable").read_bytes() == b"unique"


def test_removed_ancestor_tag_cannot_be_reused_after_confirmation(tmp_path, monkeypatch, neural_boundary):
    declare_cache(tmp_path / "cache")
    path = tmp_path / "cache/child"
    path.mkdir()
    (path / "blob").write_bytes(b"generated")
    item = apply_policy(
        measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set()), answer("remove")
    )
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection([item], home=tmp_path)
    (tmp_path / "cache/CACHEDIR.TAG").unlink()
    with pytest.raises(ValueError, match="evidence"):
        service.reassess_selection(sealed, home=tmp_path)
    result = TrashStore(tmp_path).move(sealed, open_paths=set())
    assert result.moved == 0 and (path / "blob").exists()


def test_home_level_tag_never_authorizes_entire_home(tmp_path):
    declare_cache(tmp_path)
    path = tmp_path / "personal"
    path.mkdir()
    (path / "image").write_bytes(b"unique")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert item.disposal is None
    assert not apply_policy(item, answer("remove")).selectable


def test_marker_file_itself_is_not_selectable(tmp_path):
    from jev_clean.infrastructure.scanner import candidate_from_stat

    declare_cache(tmp_path / "cache")
    path = tmp_path / "cache/CACHEDIR.TAG"
    item = candidate_from_stat(path, path.stat(), tmp_path, set())
    assert item.disposal is None
    assert not apply_policy(item, answer("remove")).selectable


def test_changed_marker_identity_rejected_even_with_same_header(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection([item], home=tmp_path)
    marker = tmp_path / "cache/CACHEDIR.TAG"
    marker.write_bytes(marker.read_bytes() + b"# changed declaration\n")
    with pytest.raises(ValueError, match="evidence"):
        service.reassess_selection(sealed, home=tmp_path)
    assert (tmp_path / "cache/nested/blob").exists()
