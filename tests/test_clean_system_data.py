import pytest
from textual.widgets import Static

from jev_clean.application.service import audit
from jev_clean.domain.models import CategoryReport
from jev_clean.ui.app import JevCleanApp


def test_clean_report_exposes_system_data_context_not_only_status(tmp_path, neural_boundary):
    report = audit(tmp_path, "clean", demo=True)
    report.categories = CategoryReport(
        "2026-09-27 12:00:00.000",
        500 * 10**9,
        20 * 10**9,
        {"com.apple.STMExtension.Documents": 200 * 10**9},
        280 * 10**9,
    )
    context = report.to_dict()["system_data"]
    assert context["native_other_bytes"] == 280 * 10**9
    assert context["residual_bytes"] == 280 * 10**9
    assert context["approved_candidate_bytes"] > 0
    assert context["category_membership"] == "unattributed"
    assert context["space_freed_by_staging"] == 0


def test_missing_native_total_is_explicit_not_zero(tmp_path, neural_boundary):
    report = audit(tmp_path, "clean", demo=True)
    report.categories = None
    data = report.to_dict()["system_data"]
    assert data["native_other_bytes"] is None
    assert data["state"] == "unavailable"


@pytest.mark.asyncio
async def test_clean_shows_system_data_before_and_through_selection(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(132, 44)) as pilot:
        await pilot.press("1")
        await pilot.pause(0.5)
        assert app.mode == "clean"
        panel = app.query_one("#system-data", Static)
        assert "System Data" in str(panel.render())
        await pilot.press("a")
        assert app.selected
        assert "System Data" in str(panel.render())
        assert "not" in str(panel.render()).lower()  # no implied per-file category proof
        selected = set(app.selected)
        await pilot.press("b")
        assert app.clean_breakdown and app.mode == "clean"
        await pilot.press("a", "enter")
        assert app.selected == selected and app.screen.id != "confirm-cleanup"
        await pilot.press("b")
        assert not app.clean_breakdown and app.selected == selected
