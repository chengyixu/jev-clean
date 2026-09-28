import os
import time

from jev_clean.domain.models import Decision, DiskNode


class ChoosingModel:
    def choose_directory(self, nodes, mode):
        return Decision(
            "n0", {f"n{i}": 1.0 if i == 0 else 0.0 for i in range(len(nodes))}, "test neural boundary", 1
        )

    def classify(self, node):
        return Decision("cache", {"cache": 1.0}, "test neural boundary", 1)

    def predict(self, item):
        return Decision("remove", {"remove": 1.0, "keep": 0.0, "review": 0.0}, "test neural boundary", 1)


def test_status_measures_model_chosen_roots_without_classifying_every_child(tmp_path):
    from jev_clean.application.exploration import explore

    root = tmp_path / "tree"
    root.mkdir()
    for i in range(230):
        (root / f"dir{i}").mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (other / "data").write_bytes(b"x" * 8192)
    result = explore(
        [DiskNode(str(root), None, True, 0), DiskNode(str(other), None, True, 0)],
        ChoosingModel(),
        "status",
        max_nodes=2,
    )
    known = {n.path: n.allocated_bytes for n in result.nodes}
    assert known[str(root)] is not None and known[str(other)] >= 8192
    assert len(result.steps) == 2


def test_clean_assesses_observed_disposable_files_not_vague_roots(tmp_path):
    from jev_clean.application.cleanup import investigate_cleanup

    p = tmp_path / "Library/Caches/app/blob"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x" * 4096)
    old = time.time() - 60 * 86400
    os.utime(p, (old, old))
    report = investigate_cleanup(tmp_path, ChoosingModel(), open_paths=set())
    assert report.stats["observed_files"] == 1
    assert report.stats["model_assessed"] == 1
    assert report.candidates[0].selectable
    assert report.steps[0].decision.backend == "test neural boundary"


def test_clean_does_not_recommend_guard_rejected_files(tmp_path):
    from jev_clean.application.cleanup import investigate_cleanup

    p = tmp_path / "Library/Caches/app/fresh"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x" * 4096)
    report = investigate_cleanup(tmp_path, ChoosingModel(), open_paths=set())
    assert not any(c.selectable for c in report.candidates)
    assert report.stats["observed_files"] == 1 and report.stats["protected_files"] == 1


def test_clean_scope_does_not_scan_unrequested_roots(tmp_path):
    from jev_clean.application.cleanup import investigate_cleanup

    for part in ("a", "b"):
        p = tmp_path / f"Library/Caches/{part}/blob"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"x" * 4096)
        old = time.time() - 60 * 86400
        os.utime(p, (old, old))
    report = investigate_cleanup(
        tmp_path, ChoosingModel(), open_paths=set(), roots=[tmp_path / "Library/Caches/a"]
    )
    assert report.stats["observed_files"] == 1
    assert all("/a/" in c.path for c in report.candidates)
