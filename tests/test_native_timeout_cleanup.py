import sys

from jev_clean.infrastructure.native import run


def test_timed_out_reader_gets_graceful_termination_and_output_is_retained():
    script = "import signal,time,sys;signal.signal(signal.SIGTERM,lambda *_:(print('stopped',flush=True),sys.exit(0)));print('ready',flush=True);time.sleep(20)"
    code, out, err = run([sys.executable, "-S", "-u", "-c", script], timeout=1)
    assert code == 124 and "ready" in out and "stopped" in out
    assert "Timeout" in err
