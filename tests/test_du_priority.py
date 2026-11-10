"""Every du runs with throttled I/O so the scan yields the disk to paging and to the person's apps.

Measured: `taskpolicy -d throttle` adds no time on an idle disk, while `taskpolicy -b` was about
4x slower and would turn more resources into deadline gaps. taskpolicy execs du in place, so
cancellation signals still reach du, and sudo stays first so it can relay them.
"""

from pathlib import Path

import pytest

from jev_clean.infrastructure import native, resources
from jev_clean.infrastructure.evidence import EvidenceCollector

THROTTLED = ["/usr/sbin/taskpolicy", "-d", "throttle", "/usr/bin/du"]


@pytest.mark.parametrize("deep", [False, True])
def test_resource_measurement_runs_du_with_throttled_io(tmp_path, monkeypatch, deep):
    seen = []
    monkeypatch.setattr(resources, "_stream_du", lambda command, *a: seen.append(command) or (1, "", "x"))
    (tmp_path / "r").mkdir()
    resources.measure_resource(tmp_path / "r", tmp_path, EvidenceCollector(tmp_path), set(), deep=deep)
    prefix = ["/usr/bin/sudo", "-n"] if deep else []
    assert seen[0][: len(prefix) + 4] == prefix + THROTTLED


def test_tree_and_single_measurements_run_du_with_throttled_io(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(native, "_stream_du", lambda command, *a: seen.append(command) or (1, "", ""))
    monkeypatch.setattr(native, "run", lambda command, *a, **k: seen.append(command) or (1, "", ""))
    native.measure_tree(tmp_path)
    native.measure_tree(Path("/Library"), deep=True)
    native.measure(tmp_path)
    assert seen[0][:4] == THROTTLED
    assert seen[1][:6] == ["/usr/bin/sudo", "-n", *THROTTLED]
    assert seen[2][:4] == THROTTLED
