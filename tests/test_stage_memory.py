"""Reports record the process footprint and MLX peak at each stage, so an incident has evidence.

Nothing is killed on these numbers; they are observations for the person and for diagnosis.
"""

import os
from datetime import datetime, timezone

from jev_clean.application import service
from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.infrastructure import native
from jev_clean.infrastructure.trash import read_private


def test_audit_records_memory_after_load_and_after_scan(tmp_path, monkeypatch, neural_boundary):
    (tmp_path / "one").mkdir()
    monkeypatch.setattr(native, "open_files", lambda: set())
    monkeypatch.setattr(native, "run", lambda *a, **k: (1, "", "unavailable"))
    report = service.audit(tmp_path, "status", roots=[tmp_path])
    memory = report.diagnostics["memory"]
    assert set(memory) == {"after_load", "after_scan"}
    for stage in memory.values():
        assert isinstance(stage["footprint_bytes"], int) and stage["footprint_bytes"] > 0
        assert isinstance(stage["mlx_peak_bytes"], int)


def test_export_records_memory_in_the_saved_plan(tmp_path, neural_boundary):
    report = AuditReport(1, datetime.now(timezone.utc).isoformat(), str(tmp_path), "clean", ScanReport())
    plan = tmp_path / "plan.json"
    service.save_plan(plan, report)
    assert "after_export" in read_private(plan)["diagnostics"]["memory"]


def test_footprint_reader_reports_this_process():
    assert native.process_footprint() > 10 * 2**20
    assert native.process_footprint(os.getpid()) > 0
