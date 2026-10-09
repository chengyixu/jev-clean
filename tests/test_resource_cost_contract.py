"""Guard the actual performance shape, not wall-clock timings on busy CI hosts."""

from test_whole_disk_scope import Model

from jev_clean.application.resources import investigate_resources
from jev_clean.infrastructure import resources


def test_directory_scan_does_not_capture_descendant_manifests_until_selection(tmp_path, monkeypatch):
    from jev_clean.infrastructure import resource_tree

    root = tmp_path / "scope"
    cache = root / "artifact"
    cache.mkdir(parents=True)
    for i in range(100):
        (cache / str(i)).write_bytes(b"x")

    def forbidden(*args, **kwargs):
        raise AssertionError("Whole descendant manifest must not be in the scan hot path")

    monkeypatch.setattr(resource_tree, "tree_manifest", forbidden)
    advisor = Model()
    result = investigate_resources(
        tmp_path, advisor, "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert advisor.calls == 1
    assert result.stats["resources_measured"] == 1
    assert result.candidates[0].path == str(cache)


def test_native_measurement_is_one_literal_resource_command_with_deadline(tmp_path, monkeypatch):
    from jev_clean.infrastructure.evidence import EvidenceCollector

    path = tmp_path / "name;not-a-command\nsecond-line"
    path.mkdir()
    calls = []

    def native(command, timeout, cancelled, progress):
        calls.append((command, timeout))
        return 0, f"64\t{path}\n", ""

    monkeypatch.setattr(resources, "_stream_du", native)
    item = resources.measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set(), deep=True)
    assert item.allocated_bytes == 65536 and item.scan_complete
    assert calls == [(["/usr/bin/sudo", "-n", "/usr/bin/du", "-x", "-k", "-s", str(path)], 30)]


def test_failed_native_resource_keeps_coverage_gap_and_model_judgment(tmp_path, monkeypatch):
    root = tmp_path / "scope"
    (root / "data").mkdir(parents=True)
    monkeypatch.setattr(resources, "_stream_du", lambda *args: (1, "", "permission denied"))
    r = investigate_resources(
        tmp_path, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert r.stats["walk_finished"] and not r.complete
    assert r.stats["measurement_gaps"] == 1
    assert r.stats["model_assessed_resources"] == 1
    assert r.candidates[0].decision.choice == "remove"
    assert not r.candidates[0].selectable
    assert r.nodes[0].allocated_bytes is None
