import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from jev_clean.infrastructure import model


def test_first_operation_automatically_provisions_missing_checkpoint(monkeypatch, tmp_path):
    calls = []

    def snapshot(download=False):
        calls.append(download)
        if not download:
            raise model.CheckpointMissing("not cached")
        return tmp_path

    monkeypatch.setattr(model, "local_snapshot", snapshot)
    monkeypatch.setattr(model, "verify_checkpoint", lambda path: calls.append("verified"))
    assert model.prepare_checkpoint() == tmp_path
    assert calls == [False, True, "verified"]


def test_cached_checkpoint_is_verified_without_network(monkeypatch, tmp_path):
    for name in (*model.REQUIRED_CHECKPOINT_FILES, "manifest.json"):
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"fixture: checksum boundary mocked below")
    calls = []
    monkeypatch.setattr(model, "local_snapshot", lambda download=False: calls.append(download) or tmp_path)
    monkeypatch.setattr(model, "verify_checkpoint", lambda path: calls.append("verified"))
    assert model.prepare_checkpoint() == tmp_path
    assert calls == [False, "verified"]


def test_failed_download_or_validation_never_reports_ready(monkeypatch, tmp_path):
    def snapshot(download=False):
        if not download:
            raise model.CheckpointMissing("not cached")
        raise RuntimeError("network failed")

    monkeypatch.setattr(model, "local_snapshot", snapshot)
    with pytest.raises(RuntimeError, match="network failed"):
        model.prepare_checkpoint()
    monkeypatch.setattr(model, "local_snapshot", lambda download=False: tmp_path)

    def invalid(path):
        raise ValueError("checksum mismatch")

    monkeypatch.setattr(model, "verify_checkpoint", invalid)
    with pytest.raises(ValueError, match="checksum mismatch"):
        model.prepare_checkpoint()


def installer():
    path = Path(__file__).parents[1] / "install.py"
    spec = importlib.util.spec_from_file_location("jev_installer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installer_verifies_the_newly_installed_model_before_ready(tmp_path):
    module = installer()
    events = []

    def run(argv, **kwargs):
        events.append(argv)
        if argv[1:3] == ["tool", "dir"]:
            return subprocess.CompletedProcess(argv, 0, stdout=str(tmp_path) + "\n")
        if "doctor" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "version": module.VERSION,
                        "model": {
                            "ready": True,
                            "model": "pinned-model",
                            "revision": "pinned-revision",
                            "weights_verified": True,
                            "smoke_inference_ms": 1.2,
                        },
                    }
                ),
            )
        return subprocess.CompletedProcess(argv, 0, stdout="")

    result = module.install("uv", runner=run)
    assert result["ready"] is True
    assert events[0][1:3] == ["tool", "install"]
    assert events[-1] == [str(tmp_path / "jev-clean/bin/jev-clean"), "doctor", "--verify-model"]


def test_installer_inference_failure_is_install_failure(tmp_path):
    module = installer()

    def run(argv, **kwargs):
        if argv[1:3] == ["tool", "dir"]:
            return subprocess.CompletedProcess(argv, 0, stdout=str(tmp_path) + "\n")
        if "doctor" in argv:
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0, stdout="")

    with pytest.raises(subprocess.CalledProcessError):
        module.install("uv", runner=run)


def test_installer_rejects_ready_from_wrong_model_or_version(tmp_path):
    module = installer()

    def run(argv, **kwargs):
        if argv[1:3] == ["tool", "dir"]:
            return subprocess.CompletedProcess(argv, 0, stdout=str(tmp_path) + "\n")
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(
                {"version": "wrong", "model": {"ready": True, "model": "wrong", "revision": "wrong"}}
            ),
        )

    with pytest.raises(RuntimeError):
        module.install("uv", runner=run)
