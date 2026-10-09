from jev_clean.infrastructure import resources
from jev_clean.infrastructure.volumes import DiskScope


def test_frontier_does_not_read_symlink_replacement_between_stat_and_listing(tmp_path, monkeypatch):
    root = tmp_path / "scope"
    root.mkdir()
    (root / "inside").write_bytes(b"fixture")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret").write_bytes(b"not in scope")
    original = resources.os.scandir
    swapped = False

    def replace_before_listing(path):
        nonlocal swapped
        if not swapped:
            swapped = True
            root.rename(tmp_path / "old-scope")
            root.symlink_to(outside, target_is_directory=True)
        return original(path)

    monkeypatch.setattr(resources.os, "scandir", replace_before_listing)
    result = resources.discover_resources(tmp_path, DiskScope([root]))
    assert not any(p.name == "secret" for p in result.paths)
    assert (outside / "secret").read_bytes() == b"not in scope"
