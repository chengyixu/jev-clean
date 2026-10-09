"""Clean is a checkbox list, not a diagnostic status matrix."""

from dataclasses import replace

import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer
from textual.widgets import DataTable, Static

from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_clean_only_shows_checkboxes_and_keeps_diagnostics_in_json(tmp_path):
    items = [
        apply_policy(replace(candidate(), id="yes", path=str(tmp_path / "cache")), answer("remove")),
        apply_policy(replace(candidate(), id="review", path=str(tmp_path / "uncertain")), answer("review")),
        apply_policy(
            replace(candidate(), id="no", path=str(tmp_path / "changed"), scan_complete=False),
            answer("remove"),
        ),
    ]
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport(items))
    report.coverage = {"complete": False}
    report.exploration = {
        "complete": False,
        "warnings": ["Private measurement gap"],
        "stats": {
            "walk_finished": True,
            "model_assessed_resources": 2000,
            "execution_unavailable": 7,
            "model_review": 9,
            "elapsed_seconds": 90,
            "scope": "startup-disk",
        },
    }
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        app.mode = "clean"
        app.accept_report(report)
        table = app.query_one("#results", DataTable)
        assert table.row_count == 1
        assert table.get_row_at(0)[0].plain == "[ ]"
        text = str(app.query_one("#summary", Static).render())
        for unwanted in (
            "?",
            "!",
            "cannot stage",
            "logged gaps",
            "exclusions",
            "resources",
            "assessed",
            "incomplete",
        ):
            assert unwanted not in text.lower()
        await pilot.press("space")
        assert table.get_row_at(0)[0].plain == "[x]"
        assert app.selected == {"yes"}
        await pilot.press("n", "a")
        assert app.selected == {"yes"}
        exported = app.report.to_dict()
        assert exported["coverage"]["complete"] is False
        assert exported["exploration"]["stats"]["execution_unavailable"] == 7
        assert len(exported["scan"]["candidates"]) == 3
        assert not (tmp_path / ".Trash").exists()
