from dataclasses import replace

import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer
from textual.widgets import DataTable

from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.ui.app import JevCleanApp
from jev_clean.ui.screens import ConfirmScreen


@pytest.mark.asyncio
async def test_native_cleanup_rows_name_the_actual_owner_action(tmp_path):
    items = [
        apply_policy(replace(candidate(id=name), operation="owner_prune", owner_tool=name), answer("remove"))
        for name in ("go", "npm", "pip")
    ]
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport(items))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test():
        app.mode = "clean"
        app.accept_report(report)
        table = app.query_one("#results", DataTable)
        labels = {table.get_row_at(i)[1].plain for i in range(table.row_count)}
        assert labels == {"go clean -cache", "npm cache verify", "pip cache purge"}
    screen = ConfirmScreen(items)
    assert "go clean -cache" in screen.detail and "npm cache verify" in screen.detail
    assert "cannot be undone" in screen.detail.lower()
