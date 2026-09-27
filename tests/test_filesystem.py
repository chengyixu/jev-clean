import os
import time
from dataclasses import replace

import pytest

from jev_clean.domain.models import Decision
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.scanner import scan_candidates
from jev_clean.infrastructure.trash import TrashStore


@pytest.fixture
def home(tmp_path):
    root = tmp_path / "home"
    root.mkdir()
    return root


def stale_file(home, name="cache.bin"):
    path = home / "Library/Caches/com.example.test" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"safe test data")
    old = time.time() - 90 * 86400
    os.utime(path, (old, old))
    return path


def scan(home):
    report = scan_candidates(home, open_paths=set())
    decision = Decision("remove", {"remove": 1.0, "keep": 0.0, "review": 0.0}, "test model boundary", 1)
    report.candidates = [apply_policy(c, decision) for c in report.candidates]
    return report


def test_scan_never_follows_symlinks_or_treats_databases_as_cache(home, tmp_path):
    file = stale_file(home)
    stale_file(home, "history.sqlite")
    secret = tmp_path / "password.txt"
    secret.write_text("outside")
    (file.parent / "linked").symlink_to(secret)
    (file.parent / "directory").symlink_to(tmp_path, target_is_directory=True)
    report = scan(home)
    assert any(c.path == str(file) for c in report.candidates)
    assert not any(c.path.endswith("password.txt") for c in report.candidates)
    assert all(not c.eligible for c in report.candidates if c.path.endswith(("linked", "history.sqlite")))


def test_scan_unknown_open_files_is_never_deletable(home):
    stale_file(home)
    assert all(not c.eligible for c in scan_candidates(home, open_paths=None).candidates)


def test_review_move_restore_and_partial_selection(home):
    first = stale_file(home, "a.bin")
    second = stale_file(home, "b.bin")
    items = scan(home).candidates
    selected = [c for c in items if c.path == str(first)]
    store = TrashStore(home)
    result = store.move(selected, open_paths=set())
    assert result.moved == 1 and result.failed == []
    assert not first.exists() and second.exists()
    restored = store.restore(result.batch_id)
    assert restored.moved == 1
    assert first.read_bytes() == b"safe test data"
    assert second.exists()


def test_changed_file_and_forged_path_are_refused(home, tmp_path):
    file = stale_file(home)
    item = next(c for c in scan(home).candidates if c.path == str(file))
    file.write_text("new valuable contents")
    store = TrashStore(home)
    result = store.move([item], open_paths=set())
    assert result.moved == 0 and result.failed and file.exists()
    outside = tmp_path / "outside"
    outside.write_text("keep")
    result = store.move([replace(item, path=str(outside), eligible=True)], open_paths=set())
    assert result.moved == 0 and outside.read_text() == "keep"


def test_active_file_blocked_at_execution_even_if_scan_was_safe(home):
    file = stale_file(home)
    item = next(c for c in scan(home).candidates if c.path == str(file))
    result = TrashStore(home).move([item], open_paths={str(file)})
    assert result.moved == 0 and file.exists()


def test_ancestor_symlink_swap_is_refused(home, tmp_path):
    file = stale_file(home)
    item = next(c for c in scan(home).candidates if c.path == str(file))
    parent = file.parent
    moved = tmp_path / "relocated"
    parent.rename(moved)
    parent.symlink_to(moved, target_is_directory=True)
    result = TrashStore(home).move([item], open_paths=set())
    assert result.moved == 0 and (moved / file.name).exists()


def test_hardlinked_files_are_protected(home):
    file = stale_file(home)
    os.link(file, file.parent / "hardlink")
    report = scan(home)
    assert all(not c.eligible for c in report.candidates)


def test_restore_will_not_overwrite(home):
    file = stale_file(home)
    item = next(c for c in scan(home).candidates if c.path == str(file))
    store = TrashStore(home)
    batch = store.move([item], open_paths=set())
    file.write_text("new contents")
    result = store.restore(batch.batch_id)
    assert result.moved == 0 and file.read_text() == "new contents"


def test_trash_symlink_is_refused(home, tmp_path):
    stale_file(home)
    (home / ".Trash").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        TrashStore(home).move(scan(home).candidates, open_paths=set())


def test_scan_limits_are_visible_and_not_eligible(home):
    for i in range(5):
        stale_file(home, f"{i}.bin")
    report = scan_candidates(home, open_paths=set(), max_files=2)
    assert not report.complete and report.warnings
    assert all(not c.eligible for c in report.candidates)
