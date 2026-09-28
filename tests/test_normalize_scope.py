def test_redundant_same_filesystem_root_is_removed(tmp_path):
    from jev_clean.infrastructure.volumes import normalize_roots

    child = tmp_path / "child"
    child.mkdir()
    assert normalize_roots([child, tmp_path, child]) == [tmp_path]
