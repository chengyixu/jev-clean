"""Fresh observed evidence is passed to Laya, never blindly accepted from a plan."""

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


def test_forged_saved_cache_claim_is_not_reused_in_fresh_model_input(tmp_path, monkeypatch, neural_boundary):
    path = tmp_path / "personal"
    path.mkdir()
    (path / "valuable").write_bytes(b"unique")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    forged = apply_policy(
        replace(item, disposal=DisposalEvidence("cachedir-tag-v1", str(path), "a" * 64)), answer("remove")
    )
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    seen = []
    from jev_clean.infrastructure.model import LayaAdvisor

    def predict(self, fresh):
        seen.append(fresh)
        return answer("review")

    monkeypatch.setattr(LayaAdvisor, "predict", predict)
    with pytest.raises(ValueError, match="Model"):
        service.prepare_selection([forged], home=tmp_path)
    assert seen[0].disposal is None
    assert "none observed" in seen[0].evidence["disposal_basis"]
    assert (path / "valuable").read_bytes() == b"unique"


def test_removed_ancestor_tag_is_observed_as_missing_on_model_recheck(tmp_path, monkeypatch, neural_boundary):
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
    seen = []
    from jev_clean.infrastructure.model import LayaAdvisor

    monkeypatch.setattr(LayaAdvisor, "predict", lambda self, fresh: seen.append(fresh) or answer("review"))
    with pytest.raises(ValueError, match="Model"):
        service.reassess_selection(sealed, home=tmp_path)
    assert seen[0].disposal is None
    assert (path / "blob").exists()


def test_home_tag_and_marker_are_not_declarations_for_their_targets(tmp_path):
    from jev_clean.infrastructure.scanner import candidate_from_stat

    declare_cache(tmp_path)
    path = tmp_path / "personal"
    path.mkdir()
    assert measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set()).disposal is None
    marker = tmp_path / "CACHEDIR.TAG"
    assert candidate_from_stat(marker, marker.stat(), tmp_path, set()).disposal is None


def test_changed_marker_within_reviewed_tree_is_a_manifest_change(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection([item], home=tmp_path)
    marker = tmp_path / "cache/CACHEDIR.TAG"
    marker.write_bytes(marker.read_bytes() + b"#changed\n")
    with pytest.raises(ValueError, match="changed"):
        service.reassess_selection(sealed, home=tmp_path)
    assert (tmp_path / "cache/nested/blob").exists()
