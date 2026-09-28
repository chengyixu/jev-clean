from pathlib import Path

from test_whole_disk_scope import Model


def test_overlapping_explicit_roots_do_not_double_assess_files(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (nested / "data").write_text("data")
    result = investigate_disk(
        home, Model(), "clean", roots=[nested, root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert result.stats["model_assessed_files"] == 1
    assert result.stats["observed_regular_files"] == 1


def test_bucket_groups_do_not_hide_disjoint_direct_files():
    from jev_clean.application.whole_disk import bucket_for

    home = Path("/Users/demo")
    assert bucket_for(Path("/private/direct-file"), home) == "/private/[files]"
    assert bucket_for(Path("/private/var/a"), home) == "/private/var"
    assert bucket_for(home / "Library" / "app-file", home) == str(home / "Library" / "[files]")
    assert bucket_for(home / "Library" / "Caches" / "file", home) == str(home / "Library" / "Caches")
