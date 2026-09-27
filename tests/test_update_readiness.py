import json
import subprocess

import pytest

from jev_clean import cli


@pytest.mark.parametrize("ready,expected", [(True, 0), (False, 1)])
def test_update_is_not_success_until_new_model_is_verified(monkeypatch, tmp_path, capsys, ready, expected):
    monkeypatch.setattr(
        cli,
        "check_update",
        lambda: {
            "latest": "0.1.1",
            "url": "https://github.com/chengyixu/jev-clean/releases/tag/v0.1.1",
            "install_spec": "jev-clean @ git+https://github.com/chengyixu/jev-clean.git@v0.1.1",
        },
    )
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli, "confirm", lambda *a: None)
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/bin/uv")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        out = (
            str(tmp_path)
            if argv[1:3] == ["tool", "dir"]
            else json.dumps({"version": "0.1.1", "model": {"ready": ready}})
        )
        return subprocess.CompletedProcess(argv, 0, stdout=out)

    monkeypatch.setattr(cli.subprocess, "run", run)
    assert cli.main(["update", "--apply"]) == expected
    output = capsys.readouterr()
    assert calls[-1] == [str(tmp_path / "jev-clean/bin/jev-clean"), "doctor", "--verify-model"]
    if not ready:
        assert '"updated": true' not in output.out
