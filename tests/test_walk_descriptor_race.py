from jev_clean.infrastructure.disk_walk import walk_user


def test_directory_replacement_cannot_redirect_walk_to_symlink_target(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    victim = root / "victim"
    victim.mkdir()
    other = tmp_path / "outside"
    other.mkdir()
    (other / "secret").write_text("not in scope")
    inode = victim.stat().st_ino

    def directory(meta):
        if meta.inode == inode:
            victim.rename(tmp_path / "saved")
            victim.symlink_to(other, target_is_directory=True)
        return True

    entries = list(
        walk_user(root, exclusions=[], issue=lambda *a: None, directory=directory, cancelled=lambda: False)
    )
    assert not any(e.path.name == "secret" for e in entries)
