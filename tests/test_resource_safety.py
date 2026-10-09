"""Execution invariants for directory resources, independent of model accuracy."""

from pathlib import Path

import pytest
from test_resource_staging import proposal

from jev_clean.application import service
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resource_tree import tree_manifest
from jev_clean.infrastructure.resources import discover_resources, measure_resource
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.infrastructure.volumes import DiskScope


def test_resource_snapshot_never_follows_internal_symlinks(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    external = tmp_path / "external"
    external.write_bytes(b"unique work")
    (tmp_path / "cache/nested/link").symlink_to(external)
    # Refresh the preview after explicitly setting up the fixture.
    item = measure_resource(Path(item.path), tmp_path, EvidenceCollector(tmp_path), set())
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection([item], home=tmp_path)
    store = TrashStore(tmp_path)
    moved = store.move(sealed, open_paths=set())
    assert moved.moved == 1, moved.failed
    assert external.read_bytes() == b"unique work"
    restored = store.restore(moved.batch_id)
    assert restored.moved == 1, restored.failed
    assert (tmp_path / "cache/nested/link").is_symlink()
    assert external.read_bytes() == b"unique work"


def test_restore_resource_cannot_overwrite_a_new_directory(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    store = TrashStore(tmp_path)
    moved = store.move(service.prepare_selection([item], home=tmp_path), open_paths=set())
    assert moved.moved == 1
    (tmp_path / "cache").mkdir()
    result = store.restore(moved.batch_id)
    assert result.moved == 0
    assert (tmp_path / "cache").is_dir()
    staged = tmp_path / ".Trash" / f"jev-clean-{moved.batch_id}"
    assert next(staged.iterdir()).joinpath("nested/blob").read_bytes() == b"resource data"


def test_permission_or_timeout_measurement_is_not_authorized(tmp_path, monkeypatch):
    from test_model_owned_judgment import answer

    from jev_clean.domain.policy import apply_policy
    from jev_clean.infrastructure import resources

    path = tmp_path / "resource"
    path.mkdir()
    monkeypatch.setattr(resources, "_stream_du", lambda *a: (124, f"4096\t{path}\n", "timed out"))
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    decided = apply_policy(item, answer("remove"))
    assert not decided.scan_complete and not decided.selectable
    assert decided.decision.choice == "remove"


def test_frontier_does_not_drop_unknown_sibling_or_include_nested_duplicates(tmp_path):
    (tmp_path / "Library/Caches/a").mkdir(parents=True)
    (tmp_path / "Library/Other/b").mkdir(parents=True)
    (tmp_path / "unknown").mkdir()
    f = discover_resources(tmp_path, DiskScope([tmp_path]))
    assert set(f.paths) == {tmp_path / "Library/Caches/a", tmp_path / "Library/Other", tmp_path / "unknown"}
    assert all(not a.is_relative_to(b) for a in f.paths for b in f.paths if a != b)


def test_manifest_detects_new_deep_entry_without_requiring_file_reads(tmp_path):
    item = proposal(tmp_path)
    before = tree_manifest(Path(item.path))
    (tmp_path / "cache/nested/new").write_bytes(b"new")
    after = tree_manifest(Path(item.path))
    assert before[0] != after[0] and after[2] == before[2] + 1


def test_plan_export_seals_resource_before_later_cli_confirmation(tmp_path, monkeypatch, neural_boundary):
    from datetime import datetime, timezone

    from jev_clean.domain.models import AuditReport, ScanReport

    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    report = AuditReport(
        1, datetime.now(timezone.utc).isoformat(), str(tmp_path), "clean", ScanReport([item])
    )
    plan = tmp_path / "plan.json"
    service.save_plan(plan, report)
    loaded = service.load_plan(plan, tmp_path)
    assert loaded[0].manifest_digest and loaded[0].member_count == 2
    assert not report.scan.candidates[0].manifest_digest
    (tmp_path / "cache/nested/blob").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        service.reassess_selection(loaded, home=tmp_path)
