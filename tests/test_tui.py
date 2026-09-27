import pytest
from textual.widgets import DataTable, Input, Static

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_two_modes_selection_help_review_cancel_and_resize(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("1")
        await pilot.pause(0.5)
        assert app.mode == "clean"
        table = app.query_one("#results", DataTable)
        assert table.row_count > 0
        await pilot.press("a")
        assert app.selected
        assert all(app.candidate_by_id[i].selectable for i in app.selected)
        await pilot.press("n")
        assert not app.selected
        await pilot.press("a", "enter")
        await pilot.pause()
        assert app.screen.id == "confirm-cleanup"
        await pilot.press("escape", "?", "escape", "2")
        await pilot.pause(0.5)
        assert app.mode == "status" and app.report.exploration["steps"]
        await pilot.press("1")
        await pilot.pause(0.5)
        await pilot.press("/")
        app.query_one("#search", Input).value = "no-matches"
        await pilot.pause()
        assert table.row_count == 0
        await pilot.resize_terminal(80, 24)
        await pilot.pause()


@pytest.mark.asyncio
async def test_model_failure_displays_error_no_selectable_rows(tmp_path, monkeypatch):
    from jev_clean.infrastructure.model import LayaAdvisor

    def fail(self):
        raise RuntimeError("Mandatory model missing")

    monkeypatch.setattr(LayaAdvisor, "load", fail)
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(100, 35)) as pilot:
        await pilot.press("1")
        await pilot.pause(0.4)
        assert not app.busy and app.report is None
        assert app.query_one("#results", DataTable).row_count == 0
        await pilot.press("a", "enter")
        assert not app.selected and app.screen.id != "confirm-cleanup"
        assert "Mandatory model missing" in str(app.query_one("#summary", Static).render())
