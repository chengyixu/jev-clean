import os
import subprocess
import sys
from pathlib import Path

import pytest

from jev_clean.infrastructure import disk_walk


def test_privileged_find_is_fixed_native_argv_and_nul_safe(monkeypatch, tmp_path):
    file = tmp_path / "name\nwith:newline"
    file.write_text("fixture")
    paths = [tmp_path, file]
    real_popen = subprocess.Popen
    calls = []

    def native_boundary(argv, **kwargs):
        calls.append(argv)
        script = (
            "import sys;sys.stdout.buffer.write("
            + repr(b"\0".join(os.fsencode(p) for p in paths) + b"\0")
            + ")"
        )
        return real_popen([sys.executable, "-S", "-c", script], **kwargs)

    monkeypatch.setattr(disk_walk.subprocess, "Popen", native_boundary)
    issues = []
    found = list(
        disk_walk.walk_privileged(
            tmp_path,
            exclusions=[],
            issue=lambda *x: issues.append(x),
            directory=lambda _: True,
            cancelled=lambda: False,
        )
    )
    assert calls[0] == ["/usr/bin/sudo", "-n", "/usr/bin/find", "-x", str(tmp_path), "-print0"]
    assert {x.path for x in found} == set(paths)
    assert not issues


def test_privileged_stat_fills_only_inaccessible_metadata(monkeypatch, tmp_path):
    from jev_clean.infrastructure import native

    path = tmp_path / "blocked"
    path.write_text("fixture")
    old_lstat = Path.lstat

    def lstat(p, *a, **k):
        if p == path:
            raise PermissionError("fixture permission")
        return old_lstat(p, *a, **k)

    monkeypatch.setattr(Path, "lstat", lstat)
    calls = []

    def reader(argv, timeout):
        calls.append(argv)
        return 0, "1:1:2:100644:501:1:7:8:1700000000.000000000:1700000000.000000000\n", ""

    monkeypatch.setattr(native, "run", reader)
    records = disk_walk.privileged_metadata([path], lambda *a: None, lambda: False)
    assert records[0].metadata.size == 7
    assert calls[0][:5] == ["/usr/bin/sudo", "-n", "/usr/bin/stat", "-f", disk_walk.STAT_FORMAT]
    assert "%N" not in disk_walk.STAT_FORMAT


def test_privileged_metadata_rejects_relative_or_escaping_paths():
    with pytest.raises(ValueError):
        disk_walk.privileged_metadata([Path("../secret")], lambda *a: None, lambda: False)


def test_closing_privileged_walk_reaps_its_process(monkeypatch, tmp_path):
    real_popen = subprocess.Popen
    processes = []
    paths = []
    for i in range(260):
        p = tmp_path / str(i)
        p.write_text("fixture")
        paths.append(p)

    def native_boundary(argv, **kwargs):
        data = b"\0".join(os.fsencode(p) for p in paths) + b"\0"
        script = (
            "import sys,time;sys.stdout.buffer.write("
            + repr(data)
            + ");sys.stdout.buffer.flush();time.sleep(30)"
        )
        proc = real_popen([sys.executable, "-S", "-u", "-c", script], **kwargs)
        processes.append(proc)
        return proc

    monkeypatch.setattr(disk_walk.subprocess, "Popen", native_boundary)
    stream = disk_walk.walk_privileged(
        tmp_path, exclusions=[], issue=lambda *a: None, directory=lambda _: True, cancelled=lambda: False
    )
    next(stream)
    stream.close()
    assert processes[0].poll() is not None
