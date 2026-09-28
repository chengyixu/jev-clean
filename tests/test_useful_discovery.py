import os
import time

from jev_clean.application.whole_disk import investigate_disk
from jev_clean.domain.models import Decision


class ChoosingModel:
    def choose_directory(self, nodes, mode):
        return Decision(
            "n0", {f"n{i}": 1.0 if i == 0 else 0.0 for i in range(len(nodes))}, "test neural boundary", 1
        )

    def classify(self, node):
        return Decision("cache", {"cache": 1.0}, "test neural boundary", 1)

    def predict(self, item):
        return Decision("remove", {"remove": 1.0, "keep": 0.0, "review": 0.0}, "test neural boundary", 1)


def test_status_finishes_wide_roots_without_immediate_child_budget_starvation(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    for i in range(230):
        (root / f"dir{i}").mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (other / "data").write_bytes(b"x" * 8192)
    result = investigate_disk(
        tmp_path,
        ChoosingModel(),
        "status",
        roots=[root, other],
        state_dir=tmp_path / "state",
        open_paths=set(),
    )
    assert result.stats["observed_regular_files"] == 1
    assert result.stats["directories_observed"] >= 232
    assert result.stats["walk_finished"] and len(result.steps) == 2
    assert sum(n.allocated_bytes or 0 for n in result.nodes) >= 8192


def test_clean_assesses_observed_disposable_files_not_vague_roots(tmp_path):
    p = tmp_path / "Library/Caches/app/blob"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x" * 4096)
    old = time.time() - 60 * 86400
    os.utime(p, (old, old))
    result = investigate_disk(
        tmp_path, ChoosingModel(), "clean", roots=[p.parent], state_dir=tmp_path / "state", open_paths=set()
    )
    assert result.stats["observed_files"] == 1 and result.stats["model_assessed_files"] == 1
    assert result.candidates[0].selectable


def test_guard_rejected_files_still_reach_model(tmp_path):
    p = tmp_path / "Library/Caches/app/fresh"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x" * 4096)
    result = investigate_disk(
        tmp_path, ChoosingModel(), "clean", roots=[p.parent], state_dir=tmp_path / "state", open_paths=set()
    )
    assert not result.candidates
    assert result.stats["model_assessed_protected_files"] == 1


def test_explicit_scope_stays_explicit(tmp_path):
    for part in ("a", "b"):
        p = tmp_path / f"Library/Caches/{part}/blob"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"x" * 4096)
        old = time.time() - 60 * 86400
        os.utime(p, (old, old))
    result = investigate_disk(
        tmp_path,
        ChoosingModel(),
        "clean",
        roots=[tmp_path / "Library/Caches/a"],
        state_dir=tmp_path / "state",
        open_paths=set(),
    )
    assert result.stats["observed_files"] == 1 and result.stats["scope"] == "custom"
    assert all("/a/" in c.path for c in result.candidates)
