from dataclasses import replace

import pytest
from test_model_owned_judgment import answer

from jev_clean.application import service
from jev_clean.infrastructure.model import LayaAdvisor
from jev_clean.infrastructure.scanner import candidate_from_stat


def test_reassessment_uses_fresh_activity_not_saved_metadata(tmp_path, monkeypatch):
    path = tmp_path / "file"
    path.write_bytes(b"fixture")
    item = candidate_from_stat(path, path.stat(), tmp_path, set())
    seen = []
    monkeypatch.setattr(service.native, "open_files", lambda: {str(path)})
    monkeypatch.setattr(LayaAdvisor, "load", lambda self: None)

    def predict(self, candidate):
        seen.append(candidate)
        return answer("keep" if candidate.open_file else "remove")

    monkeypatch.setattr(LayaAdvisor, "predict", predict)
    with pytest.raises(ValueError, match="Model"):
        service.reassess_selection([item])
    assert seen[0].open_file is True
    assert path.exists()


def test_changed_target_is_not_silently_reauthorized(tmp_path, monkeypatch):
    path = tmp_path / "file"
    path.write_bytes(b"fixture")
    item = candidate_from_stat(path, path.stat(), tmp_path, set())
    path.write_bytes(b"new owner work")
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    monkeypatch.setattr(LayaAdvisor, "load", lambda self: None)
    monkeypatch.setattr(LayaAdvisor, "predict", lambda *a: answer("remove"))
    with pytest.raises(ValueError, match="changed"):
        service.reassess_selection([item])
    assert path.read_bytes() == b"new owner work"


def test_evidence_difference_invalidates_cache(tmp_path):
    from test_whole_disk_scope import Model

    from jev_clean.infrastructure.decision_cache import DecisionCache
    from jev_clean.infrastructure.model import state_for

    path = tmp_path / "item"
    path.write_bytes(b"fixture")
    item = candidate_from_stat(path, path.stat(), tmp_path, set())
    with DecisionCache(tmp_path / "cache", Model(), [tmp_path], "clean") as cache:
        cache.put(state_for(item), answer("remove"))
        changed = replace(
            item, evidence={**item.evidence, "references": "application now references this file"}
        )
        assert cache.get(state_for(changed)) is None
        assert cache.get(state_for(item)).choice == "remove"
