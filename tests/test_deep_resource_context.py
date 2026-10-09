"""Deep cache entries must not lose their enclosing resource context."""

from jev_clean.infrastructure.evidence import EvidenceCollector


def test_deep_paths_keep_distinguishing_ancestors_without_file_contents(tmp_path):
    collector = EvidenceCollector(tmp_path)
    tail = "tool/nested/rev/objects/pack/blob.bin"
    cache = collector.collect(tmp_path / "Library/Caches" / tail)
    project = collector.collect(tmp_path / "work/projects" / tail)
    assert cache["location"] != project["location"]
    assert "Library/Caches" in cache["location"]
    assert "work/projects" in project["location"]
    assert "blob.bin" not in cache["location"]
    assert str(tmp_path) not in cache["location"]
    assert cache["regenerability"] == project["regenerability"] == "unknown"
