"""Review refresh preserves real purpose/structure facts, not stale plan assertions."""

from test_model_owned_judgment import answer

from jev_clean.application import service
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.model import LayaAdvisor, state_for
from jev_clean.infrastructure.resources import measure_resource


def test_resource_review_and_discovery_use_identical_semantic_evidence(
    tmp_path, monkeypatch, neural_boundary
):
    path = tmp_path / "Library/Caches/example"
    path.mkdir(parents=True)
    (path / "cache.bin").write_bytes(b"synthetic generated fixture")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    observed = []

    def predict(self, fresh):
        observed.append(fresh)
        return answer("remove")

    monkeypatch.setattr(LayaAdvisor, "predict", predict)
    sealed = service.prepare_selection([item], home=tmp_path)
    assert sealed[0].manifest_digest
    assert state_for(item) == state_for(observed[0])
    assert observed[0].evidence["storage_namespace"] == "macos-cache"
    assert observed[0].evidence["file_extensions"] == item.evidence["file_extensions"]


def test_forged_cache_namespace_is_discarded_on_selected_review(tmp_path, monkeypatch, neural_boundary):
    from dataclasses import replace

    import pytest

    path = tmp_path / "Pictures"
    path.mkdir()
    (path / "image.jpg").write_bytes(b"personal fixture")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    item = replace(item, evidence={**item.evidence, "storage_namespace": "macos-cache"})
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    seen = []
    monkeypatch.setattr(LayaAdvisor, "predict", lambda self, fresh: seen.append(fresh) or answer("review"))
    with pytest.raises(ValueError, match="Model"):
        service.prepare_selection([item], home=tmp_path)
    assert seen[0].evidence["storage_namespace"] == "unverified"
    assert (path / "image.jpg").exists()
