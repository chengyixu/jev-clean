import os
import signal
import sys
import time

import pytest
from test_useful_discovery import ChoosingModel

from jev_clean.infrastructure.native import _stream_du


def test_output_callback_failure_reaps_owned_reader_process():
    pids = []

    def fail(line):
        pids.append(int(line))
        raise RuntimeError("view closed")

    try:
        with pytest.raises(RuntimeError, match="view closed"):
            _stream_du(
                [sys.executable, "-u", "-c", "import os,time;print(os.getpid());time.sleep(30)"],
                5,
                lambda: False,
                fail,
            )
        with pytest.raises(ProcessLookupError):
            os.kill(pids[0], 0)
    finally:
        if pids:
            try:
                os.kill(pids[0], signal.SIGKILL)
                os.waitpid(pids[0], 0)
            except (ProcessLookupError, ChildProcessError):
                pass


def test_default_clean_budget_does_not_stop_at_first160_files(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    root = tmp_path / "Library/Caches/app"
    root.mkdir(parents=True)
    old = time.time() - 60 * 86400
    for i in range(170):
        file = root / str(i)
        file.write_bytes(b"x" * 1024)
        os.utime(file, (old, old))
    result = investigate_disk(
        tmp_path, ChoosingModel(), "clean", open_paths=set(), roots=[root], state_dir=tmp_path / "state"
    )
    assert result.stats["model_assessed"] == 170
    assert len(result.candidates) == 170
