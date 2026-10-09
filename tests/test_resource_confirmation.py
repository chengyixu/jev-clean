import pytest
from test_resource_staging import proposal

from jev_clean.application import service
from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_resource_manifest_is_bound_before_yes_no_dialog(tmp_path, monkeypatch, neural_boundary):
    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport([item]))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test() as pilot:
        app.mode = "clean"
        app.accept_report(report)
        await pilot.press("a", "enter")
        for _ in range(100):
            await pilot.pause(0.05)
            if app.screen.id == "confirm-cleanup":
                break
        assert app.screen.id == "confirm-cleanup"
        assert app.candidate_by_id[item.id].manifest_digest
        assert "directory" in app.screen.detail
        await pilot.press("n")
        assert (tmp_path / "cache/nested/blob").read_bytes() == b"resource data"
        assert not (tmp_path / ".Trash").exists()
