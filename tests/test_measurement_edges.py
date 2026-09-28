import sys
from pathlib import Path

from jev_clean.infrastructure import native


def test_timed_out_du_never_uses_unterminated_last_record():
    rows = native.parse_du_tree("/base", 124, "4\t/base/ok\n800\t/base/cut", "Timeout")
    assert {r.path for r in rows} == {"/base", "/base/ok"}
    assert rows[0].allocated_bytes == 4096 and not rows[0].complete


def test_measurement_progress_and_return_values_are_real(tmp_path):
    child = tmp_path / "data"
    child.mkdir()
    (child / "blob").write_bytes(b"x" * 8192)
    progress = []
    rows = native.measure_tree(tmp_path, progress=progress.append)
    assert any(r.path == str(child) and r.allocated_bytes >= 8192 and r.complete for r in rows)
    assert any("Measured" in line for line in progress)


def test_stream_cancel_keeps_emitted_measurement():
    lines = []
    code, out, err = native._stream_du(
        [sys.executable, "-u", "-c", "import time;print('4\\t/base/ok');time.sleep(5)"],
        3,
        lambda: bool(lines),
        lines.append,
    )
    assert code == 130 and "4\t/base/ok" in out
    assert "partial" in err.lower()


def test_deep_measurement_consumes_elevated_native_output(monkeypatch):
    calls = []

    def run(argv, timeout):
        calls.append(argv)
        return 0, "4\t/Library/Caches\n8\t/Library\n", ""

    monkeypatch.setattr(native, "run", run)
    rows = native.measure_tree(Path("/Library"), deep=True)
    assert calls[0][:3] == ["/usr/bin/sudo", "-n", "/usr/bin/du"]
    assert next(r for r in rows if r.path == "/Library").allocated_bytes == 8192


def test_open_file_elevation_is_read_only_and_fails_closed(monkeypatch):
    calls = []

    def run(argv, timeout):
        calls.append(argv)
        return 1, "", "sudo: a password is required"

    monkeypatch.setattr(native, "run", run)
    assert native.open_files(deep=True) is None
    assert calls[0][:2] == ["/usr/bin/sudo", "-n"]
    assert "-Fn" in calls[0]
