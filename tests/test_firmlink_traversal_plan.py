from pathlib import Path


def test_system_scan_prunes_aliases_only_when_data_volume_is_declared():
    from jev_clean.infrastructure.paths import aliases_covered_elsewhere

    maps = [
        (Path("/System/Volumes/Data/Users"), Path("/Users")),
        (Path("/System/Volumes/Data/Library"), Path("/Library")),
    ]
    roots = [Path("/"), Path("/System/Volumes/Data")]
    aliases = aliases_covered_elsewhere(Path("/"), roots, maps)
    assert set(aliases) == {Path("/Users"), Path("/Library"), Path("/System/Volumes/Data")}
    assert aliases_covered_elsewhere(Path("/System/Volumes/Data"), roots, maps) == []
