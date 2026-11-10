"""SIGTERM unwinds a scan like Ctrl-C: its native readers stop and none outlives jev-clean.

Before, SIGTERM killed Python at once and every running du kept walking the disk as an orphan.
"""

import os
import signal
import subprocess
import sys
import textwrap
import time

SCAN = textwrap.dedent(
    """
    import sys
    from pathlib import Path

    from jev_clean import cli
    from jev_clean.application.resources import investigate_resources
    from jev_clean.domain.models import Decision
    from jev_clean.infrastructure import resources

    root, pids = Path(sys.argv[1]), sys.argv[2]
    # A du stand-in that records its pid and keeps walking for a long time.
    resources.du_command = lambda argv, sudo=False: ["/bin/sh", "-c", f"echo $$ >> {pids}; exec sleep 60"]

    class Model:
        def choose_directory(self, nodes, mode):
            return Decision("n0", {f"n{i}": float(i == 0) for i in range(len(nodes))}, "stub", 1.0)

        def predict(self, item):
            return Decision("keep", {"keep": 1.0, "review": 0.0, "remove": 0.0}, "stub", 1.0)

    cli.terminate_on_sigterm()
    investigate_resources(root, Model(), "status", roots=[root], state_dir=root / "state", open_paths=set(),
                          measurement_timeout=60)
    """
)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_sigterm_stops_every_running_du(tmp_path):
    root = tmp_path / "scope"
    for i in range(4):
        (root / f"r{i}").mkdir(parents=True)
    pids = tmp_path / "pids"
    scan = subprocess.Popen([sys.executable, "-c", SCAN, str(root), str(pids)])
    children: list[int] = []
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and len(children) < 4:
            time.sleep(0.1)
            children = [int(p) for p in pids.read_text().split()] if pids.exists() else []
        assert len(children) == 4, "the stand-in readers never started"
        scan.send_signal(signal.SIGTERM)
        assert scan.wait(timeout=10) == 143
        time.sleep(0.5)
        assert [pid for pid in children if alive(pid)] == []
    finally:
        scan.kill()
        for pid in children:
            if alive(pid):
                os.kill(pid, signal.SIGKILL)
