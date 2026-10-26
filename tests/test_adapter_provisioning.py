"""The application provisions its pinned learned adapter; only checksum-verified bytes are installed."""

import hashlib
from pathlib import Path

import pytest

from jev_clean.infrastructure import model

WEIGHTS = b"learned fixture weights"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(model, "CLEANUP_ADAPTER_SHA256", hashlib.sha256(WEIGHTS).hexdigest())
    return tmp_path


def serve(payload, calls):
    def download(output):
        calls.append(output)
        output.write(payload)

    return download


def test_missing_adapter_is_downloaded_verified_and_installed_privately(home, monkeypatch):
    calls = []
    monkeypatch.setattr(model, "download_cleanup_adapter", serve(WEIGHTS, calls))

    path = model.cleanup_adapter_path()

    assert path == home / ".local/share/jev-clean/models" / model.CLEANUP_ADAPTER_ID / "model.safetensors"
    assert path.read_bytes() == WEIGHTS
    assert path.stat().st_mode & 0o777 == 0o600
    assert [p.name for p in path.parent.iterdir()] == ["model.safetensors"]
    assert model.cleanup_adapter_path() == path
    assert len(calls) == 1


def test_checksum_mismatch_installs_nothing(home, monkeypatch):
    monkeypatch.setattr(model, "download_cleanup_adapter", serve(b"tampered weights", []))

    with pytest.raises(ValueError, match="checksum"):
        model.cleanup_adapter_path()

    directory = home / ".local/share/jev-clean/models" / model.CLEANUP_ADAPTER_ID
    assert list(directory.iterdir()) == []


def test_tampered_installed_adapter_is_rejected_not_silently_replaced(home, monkeypatch):
    calls = []
    monkeypatch.setattr(model, "download_cleanup_adapter", serve(WEIGHTS, calls))
    path = model.cleanup_adapter_path()
    path.write_bytes(b"altered weights")

    with pytest.raises(ValueError, match="checksum"):
        model.cleanup_adapter_path()

    assert len(calls) == 1 and path.read_bytes() == b"altered weights"


def test_symlinked_model_directory_is_refused_without_writing_through_it(home, monkeypatch):
    elsewhere = home / "elsewhere"
    elsewhere.mkdir()
    models = home / ".local/share/jev-clean/models"
    models.parent.mkdir(parents=True)
    models.symlink_to(elsewhere)
    monkeypatch.setattr(model, "download_cleanup_adapter", serve(WEIGHTS, []))

    with pytest.raises(ValueError, match="symlink"):
        model.cleanup_adapter_path()

    assert list(elsewhere.iterdir()) == []
