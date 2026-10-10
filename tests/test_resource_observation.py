"""New model observations are facts, not disposal gates or invented unique-data claims."""

from jev_clean.infrastructure import evidence


def test_bounded_structural_observer_reports_media_without_contents(tmp_path):
    folder = tmp_path / "opaque"
    folder.mkdir()
    (folder / "private-holiday.jpg").write_bytes(b"private bytes never sent")
    (folder / "records.sqlite").write_bytes(b"private database never sent")
    (folder / "album.photoslibrary").mkdir()
    assert callable(getattr(evidence, "observe_children", None))
    observed = evidence.observe_children(folder, limit=64)
    assert observed["sampled_entries"] == "3"
    assert ".jpg" in observed["file_extensions"] and ".sqlite" in observed["file_extensions"]
    assert ".photoslibrary" in observed["directory_extensions"]
    assert observed["unique_data_status"] == "not established by metadata"
    assert "private-holiday" not in str(observed) and "private bytes" not in str(observed)


def test_bounded_observer_does_not_follow_symlinks_and_reports_partial_sample(tmp_path):
    folder = tmp_path / "resource"
    folder.mkdir()
    (folder / "outside-link").symlink_to(tmp_path, target_is_directory=True)
    for i in range(12):
        (folder / str(i)).write_bytes(b"fixture")
    assert callable(getattr(evidence, "observe_children", None))
    observed = evidence.observe_children(folder, limit=4)
    assert observed["sampled_entries"] == "4"
    assert observed["observation_scope"] == "partial immediate-entry sample; no subtree purity claim"
    assert not any("disposable" in k or "eligible" in k for k in observed)


def test_modified_cache_evidence_does_not_claim_no_unique_work(tmp_path):
    folder = tmp_path / "cache"
    folder.mkdir()
    (folder / "work.py").write_bytes(b"modified project")
    assert callable(getattr(evidence, "observe_children", None))
    observed = evidence.observe_children(folder)
    assert observed["unique_data_status"] == "not established by metadata"
    assert observed["runtime_references"] == "not established by entry inspection"
