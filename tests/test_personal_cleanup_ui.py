import pytest
from test_model_owned_judgment import answer
from textual.widgets import DataTable

from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_pictures_and_renamed_data_never_become_checkboxes_from_remove_alone(tmp_path):
    items = []
    for name in ("Pictures", "renamed-user-data", "cache-looking-name"):
        path = tmp_path / name
        path.mkdir()
        (path / "unique.bin").write_bytes(b"unique work")
        item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
        items.append(apply_policy(item, answer("remove")))
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport(items))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test() as pilot:
        app.mode = "clean"
        app.accept_report(report)
        assert app.query_one("#results", DataTable).row_count == 0
        await pilot.press("a", "space", "enter")
        assert not app.selected
        assert app.screen.id != "confirm-cleanup"
        exported = report.to_dict()["scan"]["candidates"]
        assert all(c["decision"]["choice"] == "remove" and not c["selectable"] for c in exported)
        assert not (tmp_path / ".Trash").exists()
