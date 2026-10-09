from test_whole_disk_scope import Model

from jev_clean.application.resources import investigate_resources


def test_unknown_personal_resource_is_measured_not_announced_as_removal(tmp_path):
    root = tmp_path / "scope"
    personal = root / "Pictures"
    personal.mkdir(parents=True)
    (personal / "unique.bin").write_bytes(b"unique work")
    lines = []
    result = investigate_resources(
        tmp_path,
        Model(),
        "clean",
        roots=[root],
        state_dir=tmp_path / "state",
        open_paths=set(),
        progress=lines.append,
    )
    row = next(line for line in lines if str(personal) in line)
    assert "remove" not in row.lower()
    assert "Measured" in row
    assert result.candidates[0].decision.choice == "remove"
    assert not result.candidates[0].selectable
