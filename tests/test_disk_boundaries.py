from pathlib import Path

import pytest

from jev_clean.infrastructure.disk_walk import parse_stat_batch
from jev_clean.infrastructure.paths import logical_path


def test_native_stat_parser_uses_ordinals_not_untrusted_filenames():
    paths = [Path("/fixture/a\n123:bad"), Path("/fixture/second")]
    records = parse_stat_batch(
        paths,
        "1:1:10:100644:501:1:12:8:1700000000.000000000:1700000000.000000000\n2:1:11:100644:501:1:20:8:1700000001.000000000:1700000001.000000000\n",
    )
    assert records[0].path == paths[0] and records[1].path == paths[1]
    assert records[0].metadata.mtime_ns == 1700000000000000000
    with pytest.raises(ValueError):
        parse_stat_batch(paths, "3:1:10:100644:501:1:12:8:1:1")


def test_apple_data_alias_maps_to_same_guard_path():
    maps = [(Path("/System/Volumes/Data/Users"), Path("/Users"))]
    assert logical_path(Path("/System/Volumes/Data/Users/demo/Library/Caches/x"), maps) == Path(
        "/Users/demo/Library/Caches/x"
    )
    assert logical_path(Path("/System/Volumes/Data/.private-volume-data"), maps) == Path(
        "/System/Volumes/Data/.private-volume-data"
    )


def test_resume_reuses_only_identical_state_and_detects_file_change(tmp_path):
    from test_whole_disk_scope import Model

    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").write_text("first")
    model = Model()
    first = investigate_disk(
        home, model, "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    (root / "a").write_bytes(b"x" * 1000000)
    second = investigate_disk(
        home, model, "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert first.stats["fresh_model_inferences"] == 1
    assert second.stats["fresh_model_inferences"] == 1


def test_whole_disk_mode_is_the_service_default(monkeypatch, tmp_path, neural_boundary):
    from jev_clean.application import service
    from jev_clean.domain.models import ExplorationResult
    from jev_clean.infrastructure import native

    seen = []

    def whole(home, advisor, mode, **kwargs):
        seen.append(kwargs["roots"])
        return ExplorationResult(stats={"coverage": {"scope": "startup-disk"}})

    monkeypatch.setattr(service, "investigate_disk", whole)
    monkeypatch.setattr(native, "run", lambda *a, **k: (1, "", "unavailable"))
    monkeypatch.setattr(native, "open_files", lambda: set())
    for mode in ("clean", "status"):
        report = service.audit(tmp_path, mode)
        assert report.coverage["scope"] == "startup-disk"
    assert seen == [None, None]
