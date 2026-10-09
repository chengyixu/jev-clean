"""Resource granularity: thousands of descendants do not mean thousands of neural calls."""

from jev_clean.application import service
from jev_clean.infrastructure import native


def test_clean_uses_one_decision_for_a_large_directory_not_each_file(tmp_path, monkeypatch, neural_boundary):
    root = tmp_path / "scope"
    cache = root / "generated"
    cache.mkdir(parents=True)
    for i in range(1100):
        (cache / f"part-{i}").write_bytes(b"x" * 1024)
    monkeypatch.setattr(native, "open_files", lambda: set())
    calls = []
    from test_model_owned_judgment import answer

    from jev_clean.infrastructure.model import LayaAdvisor

    def predict(self, item):
        calls.append(item)
        return answer("remove")

    monkeypatch.setattr(LayaAdvisor, "predict", predict)
    report = service.audit(tmp_path, "clean", roots=[root])
    assert len(calls) == 1
    item = report.scan.candidates[0]
    assert item.path == str(cache)
    assert item.unit == "directory"
    assert item.allocated_bytes >= 1100 * 1024
    assert report.exploration["stats"]["model_assessed_resources"] == 1
    assert report.coverage["granularity"] == "resource"
    assert "model_assessed_files" not in report.exploration["stats"]
    assert not item.manifest_digest  # Exact membership is prepared only for selected review.


def test_nested_custom_roots_do_not_double_count_resource_bytes(tmp_path, monkeypatch, neural_boundary):
    root = tmp_path / "scope"
    child = root / "cache"
    child.mkdir(parents=True)
    (child / "blob").write_bytes(b"x" * 8192)
    monkeypatch.setattr(native, "open_files", lambda: set())
    report = service.audit(tmp_path, "clean", roots=[root, child])
    assert len(report.scan.candidates) == 1
    assert report.scan.candidates[0].path == str(child)


def test_symlink_resources_are_not_followed(tmp_path, monkeypatch, neural_boundary):
    root = tmp_path / "scope"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (other / "private").write_bytes(b"keep")
    (root / "alias").symlink_to(other, target_is_directory=True)
    monkeypatch.setattr(native, "open_files", lambda: set())
    report = service.audit(tmp_path, "clean", roots=[root])
    assert not report.scan.candidates
    assert report.coverage["symlinks_observed"] == 1
    assert (other / "private").read_bytes() == b"keep"


def test_cancellation_never_yields_actionable_resources(tmp_path, monkeypatch, neural_boundary):
    (tmp_path / "cache").mkdir()
    monkeypatch.setattr(native, "open_files", lambda: set())
    report = service.audit(tmp_path, "clean", roots=[tmp_path], cancelled=lambda: True)
    assert not report.scan.complete
    assert not any(c.selectable for c in report.scan.candidates)
