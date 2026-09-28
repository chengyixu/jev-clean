import pytest
from textual.widgets import Static

from jev_clean.application.service import audit
from jev_clean.domain.models import CategoryReport
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_displayed_number_comes_from_report_and_source_is_available(tmp_path, neural_boundary):
    report = audit(tmp_path, "clean", demo=True)
    report.demo = False
    report.categories = CategoryReport(
        "2025-01-01 12:34:56.789",
        500000000000,
        20000000000,
        {"com.apple.STMExtension.Documents": 356543210988},
        123456789012,
    )
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 30)) as pilot:
        app.mode = "clean"
        app.accept_report(report)
        text = str(app.query_one("#summary", Static).render())
        assert "123.46 GB" in text and "12:34:56" in text and "macOS log" in text
        await pilot.press("s")
        contents = " ".join(str(w.render()) for w in app.screen.query(Static))
        assert "123456789012" in contents and "StorageManagementService" in contents
        await pilot.press("escape")
        report.categories = CategoryReport(
            "2026-09-28 10:12:00.000",
            200000000000,
            20000000000,
            {"com.apple.STMExtension.Documents": 100000000000},
            80000000000,
        )
        app.accept_report(report)
        text = str(app.query_one("#summary", Static).render())
        assert "80.00 GB" in text and "123.46" not in text
