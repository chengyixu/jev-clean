import hashlib
import json
import types

import pytest

from jev_clean.infrastructure import model


def fixture_checkpoint(tmp_path, monkeypatch):
    files = {}
    for name in model.REQUIRED_CHECKPOINT_FILES:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        content = ("fixture for " + name).encode()
        file.write_bytes(content)
        files[name] = {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    data = json.dumps({"files": files}).encode()
    (tmp_path / "manifest.json").write_bytes(data)
    monkeypatch.setattr(model, "MANIFEST_SHA256", hashlib.sha256(data).hexdigest())
    return tmp_path


def test_pinned_checksum_validation_rejects_tampering(tmp_path, monkeypatch):
    checkpoint = fixture_checkpoint(tmp_path, monkeypatch)
    model.verify_checkpoint(checkpoint)
    target = checkpoint / "model.safetensors"
    content = target.read_bytes()
    target.write_bytes(b"x" * len(content))
    with pytest.raises(ValueError, match="checksum mismatch"):
        model.verify_checkpoint(checkpoint)


def test_pinned_manifest_rejects_mutated_integrity_contract(tmp_path, monkeypatch):
    checkpoint = fixture_checkpoint(tmp_path, monkeypatch)
    (checkpoint / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="manifest checksum"):
        model.verify_checkpoint(checkpoint)


def test_checkpoint_incomplete_is_not_ready(tmp_path, monkeypatch):
    checkpoint = fixture_checkpoint(tmp_path, monkeypatch)
    (checkpoint / "model.safetensors").write_bytes(b"partial")
    with pytest.raises(ValueError, match="size mismatch"):
        model.verify_checkpoint(checkpoint)


def test_model_load_uses_verified_automatic_checkpoint(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(model.LayaAdvisor, "_shared", None)
    monkeypatch.setattr(model, "prepare_checkpoint", lambda: calls.append("prepare") or tmp_path)
    backend = object()
    monkeypatch.setitem(
        __import__("sys").modules,
        "laya_mlx",
        types.SimpleNamespace(load=lambda path: calls.append(path) or backend),
    )
    advisor = model.LayaAdvisor()
    advisor.load()
    assert calls == ["prepare", str(tmp_path)]
    assert model.LayaAdvisor._shared is backend


def test_readiness_runs_inference_and_rejects_model_error(monkeypatch):
    monkeypatch.setattr(model.LayaAdvisor, "load", lambda self: None)

    def fail(*args, **kwargs):
        raise RuntimeError("GPU unavailable")

    monkeypatch.setattr(model.LayaAdvisor, "decide", fail)
    with pytest.raises(RuntimeError, match="GPU unavailable"):
        model.verify_model_ready()
