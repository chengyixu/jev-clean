"""Stopping a native reader must never raise and never block on pipes a grandchild still holds.

A du stuck in kernel I/O, or any child that ignores SIGTERM while a grandchild keeps the pipes
open, used to make the second communicate() raise TimeoutExpired. That escaped the scan loop
and aborted the whole scan, discarding every measurement already made.
"""

import time

from jev_clean.infrastructure import native

STUBBORN = ["/bin/sh", "-c", "trap '' TERM; echo partial; sleep 6 & wait"]


def test_stream_stop_returns_partial_output_when_child_ignores_terminate():
    started = time.monotonic()
    code, out, err = native._stream_du(STUBBORN, 0.5, lambda: False, lambda _: None)
    assert time.monotonic() - started < 4
    assert code == 124 and "partial" in out and "partial data retained" in err


def test_stream_cancel_returns_130_without_raising():
    calls = iter([False, True])
    code, out, _ = native._stream_du(STUBBORN, 10, lambda: next(calls, True), lambda _: None)
    assert code == 130


def test_run_stop_returns_partial_output_when_child_ignores_terminate():
    started = time.monotonic()
    code, out, err = native.run(STUBBORN, 0.5)
    assert time.monotonic() - started < 4
    assert code == 124 and "partial" in out and "Timeout" in err


def test_run_keeps_large_listings_such_as_system_wide_lsof():
    code, out, _ = native.run(["/bin/sh", "-c", "head -c 6000000 /dev/zero | tr '\\0' 'x'"], 10)
    assert code == 0 and len(out) == 6_000_000


def test_sudo_wrapped_reader_is_relayed_terminate_and_never_sigkilled(monkeypatch):
    sent = []

    class Process:
        args = ["/usr/bin/sudo", "-n", "/usr/bin/du"]

        def poll(self):
            return None

        def terminate(self):
            sent.append("TERM")

        def kill(self):
            sent.append("KILL")

        def wait(self, timeout):
            raise native.subprocess.TimeoutExpired(self.args, timeout)

    native._stop(Process(), None, {}, 0, drain_seconds=0)
    assert sent == ["TERM"]
