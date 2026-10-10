"""Clean reviews paths, not command actions or their unknown prune totals."""

from dataclasses import replace

import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer
from textual.widgets import DataTable, Static

from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_file_list_excludes_commands_and_their_store_sizes(tmp_path):
    file = apply_policy(
        replace(
            candidate(), id="file", path=str(tmp_path / "Library/Caches/app"), allocated_bytes=12_000_000
        ),
        answer("remove"),
    )
    command = apply_policy(
        replace(
            candidate(),
            id="command",
            path=str(tmp_path / ".cache/uv"),
            operation="owner_prune",
            owner_tool="uv",
            allocated_bytes=4_000_000_000,
        ),
        answer("remove"),
    )
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport([command, file]))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test() as pilot:
        app.mode = "clean"
        app.accept_report(report)
        table = app.query_one("#results", DataTable)
        assert table.row_count == 1
        assert table.get_row_at(0)[1].plain == "~/Library/Caches/app"
        await pilot.press("a")
        assert app.selected == {"file"}
        summary = str(app.query_one("#summary", Static).render())
        assert "12.00 MB" in summary and "4.00 GB" not in summary
        assert report.system_data["approved_candidate_bytes"] == 12_000_000
        assert len(report.to_dict()["scan"]["candidates"]) == 2  # reporting stays honest
