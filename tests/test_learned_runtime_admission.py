"""Learned model decisions, not CACHEDIR.TAG gates, own the next preview's judgments."""

from dataclasses import replace

from test_contracts import candidate
from test_model_owned_judgment import answer

from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure import model


def test_remove_permission_has_no_cache_tag_requirement():
    item = replace(candidate(), disposal=None)
    result = apply_policy(item, answer("remove"))
    assert result.selectable
    assert not apply_policy(item, answer("keep")).selectable
    assert not apply_policy(item, answer("review")).selectable


def test_learned_resource_prediction_calls_probability_ensemble_not_old_action_question(monkeypatch):
    assert callable(getattr(model, "predict_cleanup", None)), "Trained Laya inference adapter not wired"
    seen = []

    def predict(backend, item):
        seen.append(item)
        return answer("review")

    monkeypatch.setattr(model, "predict_cleanup", predict)
    monkeypatch.setattr(model.LayaAdvisor, "_shared", object())
    result = model.LayaAdvisor().predict(candidate())
    assert result.choice == "review" and len(seen) == 1


def test_learned_artifact_checksum_tampering_is_rejected(tmp_path, monkeypatch):
    assert callable(getattr(model, "verify_cleanup_adapter", None))
    import hashlib

    path = tmp_path / "weights.safetensors"
    path.write_bytes(b"fixture learned weights")
    monkeypatch.setattr(model, "CLEANUP_ADAPTER_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    model.verify_cleanup_adapter(path)
    path.write_bytes(b"altered learned weights")
    import pytest

    with pytest.raises(ValueError, match="checksum"):
        model.verify_cleanup_adapter(path)
