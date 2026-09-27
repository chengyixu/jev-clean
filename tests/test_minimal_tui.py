import threading

import pytest
from textual.widgets import DataTable, OptionList, RichLog, Static

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_home_is_just_two_choices_at_small_terminal(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        assert app.stage == "menu"
        menu = app.query_one("#menu", OptionList)
        assert menu.display and menu.option_count == 2
        assert not app.query_one("#trace", RichLog).display
        assert not app.query_one("#results", DataTable).display
        assert not list(app.query("Header, Footer, ProgressBar"))
        await pilot.press("down", "enter")
        # Status starts directly, not through the Clean sudo question.
        await pilot.pause(0.1)
        assert app.mode == "status"
        assert app.screen.id != "sudo-question"


@pytest.mark.asyncio
async def test_clean_permission_then_logs_then_review(tmp_path, monkeypatch, neural_boundary):
    from jev_clean.application.service import demo_report
    from jev_clean.infrastructure.model import LayaAdvisor
    from jev_clean.ui import app as module

    release = threading.Event()

    def investigation(home, mode, **kwargs):
        kwargs["progress"]("Inspecting cache…")
        release.wait(timeout=5)
        return demo_report(home, mode, LayaAdvisor(), lambda _: None)

    monkeypatch.setattr(module, "audit", investigation)
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("1")
        assert app.screen.id == "sudo-question"
        await pilot.press("n")
        await pilot.pause(0.1)
        assert app.stage == "running"
        assert app.query_one("#trace", RichLog).display
        assert not app.query_one("#results", DataTable).display
        assert not app.query_one("#menu", OptionList).display
        release.set()
        await pilot.pause(0.4)
        assert app.stage == "review"
        assert app.query_one("#results", DataTable).display
        assert not app.query_one("#trace", RichLog).display
        await pilot.press("a", "enter")
        assert app.screen.id == "confirm-cleanup"
        assert app.focused.id == "no"
        await pilot.press("enter")
        assert app.stage == "review" and app.report is not None
        assert not (tmp_path / ".Trash").exists()


@pytest.mark.asyncio
async def test_status_has_percent_rows_without_dashboard(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("2")
        await pilot.pause(0.5)
        assert app.stage == "status"
        table = app.query_one("#results", DataTable)
        assert table.row_count > 0
        rendered = " ".join(str(cell) for key in table.rows for cell in table.get_row(key))
        assert "%" in rendered and "█" in rendered
        assert "measured" in str(app.query_one("#summary", Static).render()).lower()
        assert not app.query_one("#trace", RichLog).display
        await pilot.press("escape")
        assert app.stage == "menu"
