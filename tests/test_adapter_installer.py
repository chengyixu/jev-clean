"""Learned artifact installation must not write through arbitrary symlinks."""

import hashlib

import pytest
from test_turnkey_install import installer


def test_verified_adapter_install_is_atomic_private_and_reusable(tmp_path, monkeypatch):
    m = installer()
    source = tmp_path / "source.safetensors"
    source.write_bytes(b"learned fixture")
    monkeypatch.setattr(m, "ADAPTER_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    from pathlib import Path

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert callable(getattr(m, "provision_adapter", None))
    target = m.provision_adapter(source)
    assert target.read_bytes() == source.read_bytes()
    assert target.stat().st_mode & 0o777 == 0o600
    assert m.provision_adapter(None) == target


def test_symlink_temporary_target_never_overwrites_other_file(tmp_path, monkeypatch):
    m = installer()
    source = tmp_path / "source.safetensors"
    source.write_bytes(b"learned fixture")
    monkeypatch.setattr(m, "ADAPTER_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    from pathlib import Path

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    directory = tmp_path / ".local/share/jev-clean/models" / m.ADAPTER_ID
    directory.mkdir(parents=True)
    valuable = tmp_path / "valuable"
    valuable.write_bytes(b"keep")
    (directory / "model.new").symlink_to(valuable)
    assert callable(getattr(m, "provision_adapter", None))
    target = m.provision_adapter(source)
    assert valuable.read_bytes() == b"keep"
    assert target.read_bytes() == source.read_bytes()


def test_bad_adapter_never_replaces_existing_verified_artifact(tmp_path, monkeypatch):
    m = installer()
    source = tmp_path / "source.safetensors"
    source.write_bytes(b"learned fixture")
    monkeypatch.setattr(m, "ADAPTER_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    from pathlib import Path

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert callable(getattr(m, "provision_adapter", None))
    target = m.provision_adapter(source)
    source.write_bytes(b"invalid")
    with pytest.raises(ValueError, match="checksum"):
        m.provision_adapter(source)
    assert target.read_bytes() == b"learned fixture"
