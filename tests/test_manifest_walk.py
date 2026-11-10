"""Manifest sealing can be stopped, keeps memory independent of tree size, and runs once per apply."""

import os
import time
from pathlib import Path

import pytest
from test_resource_staging import proposal

from jev_clean.application import service
from jev_clean.domain.models import Cancelled
from jev_clean.infrastructure import resource_tree
from jev_clean.infrastructure.resource_tree import tree_manifest


def tree(root: Path, directories: int = 5) -> Path:
    for i in range(directories):
        (root / f"d{i}").mkdir(parents=True)
        (root / f"d{i}/file").write_bytes(b"x" * 5000)
    return root


def test_walk_stops_when_cancelled(tmp_path):
    root = tree(tmp_path / "t")
    calls = []

    def cancelled():
        calls.append(1)
        return len(calls) > 1

    with pytest.raises(Cancelled):
        tree_manifest(root, cancelled=cancelled)


def test_only_multi_link_files_are_remembered_and_sizes_match_du(tmp_path, monkeypatch):
    root = tree(tmp_path / "t")
    os.link(root / "d0/file", root / "d1/again")
    remembered = []
    real = resource_tree._allocated

    def spy(st, seen):
        size = real(st, seen)
        remembered.append(len(seen))
        return size

    monkeypatch.setattr(resource_tree, "_allocated", spy)
    digest, size, count = tree_manifest(root)
    assert max(remembered) == 1  # the one inode with two links
    blocks = os.stat(root).st_blocks + sum(
        os.stat(p).st_blocks for p in {*root.rglob("*")} - {root / "d1/again"}
    )
    assert size == blocks * 512 and count == 11


def test_refresh_selection_honours_cancel(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    with pytest.raises(Cancelled):
        service.prepare_selection([item], home=tmp_path, cancelled=lambda: True)


def test_apply_walks_each_tree_once_at_staging(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection([item], home=tmp_path)
    walks = []
    real = resource_tree.tree_manifest
    monkeypatch.setattr(service, "tree_manifest", lambda *a, **k: walks.append("reassess") or real(*a, **k))
    service.reassess_selection(sealed, home=tmp_path)
    assert walks == []


def test_overlap_check_is_complete_and_scales(tmp_path):
    paths = [Path(f"/r/{i:05d}") for i in range(20000)]
    started = time.monotonic()
    service.check_disjoint(paths)
    assert time.monotonic() - started < 1
    with pytest.raises(ValueError, match="overlap"):
        service.check_disjoint([Path("/a/b/c"), Path("/a/x"), Path("/a/b")])
    with pytest.raises(ValueError, match="overlap"):
        service.check_disjoint([Path("/a"), Path("/b"), Path("/a")])
    service.check_disjoint([Path("/a/b"), Path("/a/bc"), Path("/a/b c")])
