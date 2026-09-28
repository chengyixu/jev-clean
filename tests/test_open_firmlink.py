from pathlib import Path

from jev_clean.infrastructure import native, paths


def test_open_data_volume_file_matches_logical_cleanup_path(monkeypatch):
    monkeypatch.setattr(
        native, "run", lambda *a, **k: (0, "n/System/Volumes/Data/Users/demo/Library/Caches/open\n", "")
    )
    monkeypatch.setattr(paths, "firmlinks", lambda: [(Path("/System/Volumes/Data/Users"), Path("/Users"))])
    assert native.open_files() == {"/Users/demo/Library/Caches/open"}
