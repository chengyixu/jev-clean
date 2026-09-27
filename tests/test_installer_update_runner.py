import json
import subprocess
from pathlib import Path

from jev_clean import cli


def test_update_works_with_uv_provisioned_privately_by_installer(monkeypatch, tmp_path, capsys):
    bootstrap = tmp_path / ".local/share/jev-clean/installer/bin/uv"
    bootstrap.parent.mkdir(parents=True)
    bootstrap.write_text("external runner fixture")
    bootstrap.chmod(0o700)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(cli.shutil, "which", lambda _: None)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli, "confirm", lambda *args: None)
    monkeypatch.setattr(
        cli,
        "check_update",
        lambda: {
            "latest": "0.1.1",
            "url": "https://github.com/chengyixu/jev-clean/releases/tag/v0.1.1",
            "install_spec": "fixture",
        },
    )
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        out = (
            str(tmp_path / "tools")
            if argv[1:3] == ["tool", "dir"]
            else json.dumps({"version": "0.1.1", "model": {"ready": True}})
        )
        return subprocess.CompletedProcess(argv, 0, stdout=out)

    monkeypatch.setattr(cli.subprocess, "run", run)
    assert cli.main(["update", "--apply"]) == 0
    assert calls[0][0] == str(bootstrap)
    assert '"updated": true' in capsys.readouterr().out
