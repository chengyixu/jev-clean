import threading

import pytest
from textual.widgets import DataTable, Static

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_demo_delete_requires_explicit_yes_and_changes_no_files(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("1")
        await pilot.pause(0.4)
        await pilot.press("a")
        await pilot.pause(0.1)
        assert "[x]" in app.export_screenshot()
        await pilot.press("enter")
        assert app.screen.id == "confirm-cleanup"
        await pilot.press("2")
        assert app.mode == "clean" and not app.busy
        await pilot.press("y")
        await pilot.pause(0.1)
        assert app.stage == "done" and not (tmp_path / ".Trash").exists()
        assert "No files" in str(app.query_one("#summary", Static).render())
        await pilot.press("escape")
        assert app.stage == "menu"


@pytest.mark.asyncio
async def test_sudo_cancel_returns_to_menu_without_running_scan(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("1", "escape")
        assert app.stage == "menu" and app.report is None and not app.busy


@pytest.mark.asyncio
async def test_cancel_running_model_cannot_leave_actionable_review(tmp_path, neural_boundary, monkeypatch):
    from jev_clean.application.service import demo_report
    from jev_clean.infrastructure.model import LayaAdvisor
    from jev_clean.ui import app as module

    release = threading.Event()

    def blocked(home, mode, **kwargs):
        release.wait(timeout=5)
        return demo_report(home, mode, LayaAdvisor(), lambda _: None)

    monkeypatch.setattr(module, "audit", blocked)
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("1", "escape")
        release.set()
        await pilot.pause(0.4)
        assert app.stage == "menu" and app.report is None and not app.selected


@pytest.mark.asyncio
async def test_small_terminal_results_and_hint_fit_without_dashboard(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("2")
        await pilot.pause(0.4)
        assert app.query_one("#results", DataTable).region.bottom <= 24
        assert app.query_one("#hint", Static).region.bottom <= 24
        await pilot.resize_terminal(60, 20)
        await pilot.pause(0.1)
        assert app.query_one("#results", DataTable).region.height >= 5
        assert app.query_one("#hint", Static).region.bottom <= 20
