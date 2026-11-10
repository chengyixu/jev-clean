"""The scan adds work only while macOS reports normal memory pressure.

At warn (2) it submits no new native measurement and waits; at critical (4) it stops through
the same partial-report path as cancel. It never kills anything.
"""

import platform

import pytest
from test_whole_disk_scope import Model

from jev_clean.application import resources
from jev_clean.infrastructure import native

STOPPED = "Stopped: system memory pressure critical"
KERNEL_READER = native.memory_pressure  # captured before the hermetic conftest substitute


def scope(tmp_path, count=6):
    root = tmp_path / "scope"
    for i in range(count):
        (root / f"r{i}").mkdir(parents=True)
        (root / f"r{i}/blob").write_bytes(b"fixture")
    return root


def readings(monkeypatch, sequence):
    """Pressure readings in order; the last value repeats. Records the level each submission saw."""
    state = {"seen": [], "submitted": []}
    values = list(sequence)

    def pressure():
        level = values.pop(0) if len(values) > 1 else values[0]
        state["seen"].append(level)
        return level

    real = resources.measure_resource

    def measure(*args, **kwargs):
        state["submitted"].append(state["seen"][-1])
        return real(*args, **kwargs)

    monkeypatch.setattr(native, "memory_pressure", pressure)
    monkeypatch.setattr(resources, "measure_resource", measure)
    return state


def scan(tmp_path, root, **kwargs):
    return resources.investigate_resources(
        tmp_path, Model(), "status", roots=[root], state_dir=tmp_path / "state", open_paths=set(), **kwargs
    )


def test_critical_pressure_stops_the_scan_with_a_partial_report(tmp_path, monkeypatch):
    root = scope(tmp_path)
    state = readings(monkeypatch, [1, 1, 4])
    result = scan(tmp_path, root)
    assert set(state["submitted"]) <= {1}
    assert len(state["submitted"]) < 6
    assert STOPPED in result.warnings
    assert not result.stats["walk_finished"] and not result.complete


def test_warn_pressure_pauses_new_measurements_until_normal(tmp_path, monkeypatch):
    root = scope(tmp_path)
    state = readings(monkeypatch, [2, 2, 2, 2, 1])
    notes = []
    result = scan(tmp_path, root, progress=notes.append)
    assert state["submitted"] == [1] * 6
    assert "Paused · memory pressure" in notes
    assert result.stats["walk_finished"] and STOPPED not in result.warnings


def test_cancel_is_honoured_while_paused(tmp_path, monkeypatch):
    root = scope(tmp_path)
    state = readings(monkeypatch, [2])
    result = scan(tmp_path, root, cancelled=lambda: len(state["seen"]) > 5)
    assert state["submitted"] == []
    assert not result.stats["walk_finished"]


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS kernel reading")
def test_real_reader_reports_a_kernel_pressure_level():
    assert KERNEL_READER() in (1, 2, 4)
