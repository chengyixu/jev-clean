"""Status user journeys: mouse drilldown, keyboard parity and non-destructive selection."""

import pytest
from test_status_map_contract import LABELS, item, report
from textual.widgets import DataTable, Static

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_status_map_mouse_drilldown_back_and_selection(tmp_path):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(110, 35)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        assert app.query("#storage-map"), "Status still renders flat rows instead of an interactive treemap"
        from jev_clean.ui.storage_map import StorageMap, TreemapCanvas

        view = app.query_one(StorageMap)
        canvas = app.query_one(TreemapCanvas)
        assert view.display and not app.query_one("#results", DataTable).display
        assert tuple(e.label for e in view.current.children[:10]) == LABELS
        await pilot.pause()
        apps = next(t for t in canvas.tiles if t.entry.label == "Applications")
        await pilot.click(canvas, offset=(apps.x + apps.width // 2, apps.y + apps.height // 2))
        await pilot.pause()
        assert view.current.label == "Applications"
        assert "Applications" in str(app.query_one("#summary", Static).render())
        await pilot.press("a")
        assert app.selected == {c.id for c in report().scan.candidates}
        assert not (tmp_path / ".Trash").exists()
        await pilot.press("escape")
        assert view.current.id == "disk" and app.selected
        await pilot.resize_terminal(80, 24)
        assert app.selected and view.current.id == "disk"
        await pilot.press("n")
        assert not app.selected


@pytest.mark.asyncio
async def test_all_only_ready_actual_paths_and_confirmation_defaults_no(tmp_path):
    r = report()
    r.scan.candidates.extend(
        [
            item("/keep", "keep"),
            item("/review", "review"),
            item("/blocked", ready=False),
            item("/commands", operation="owner_prune"),
        ]
    )
    r.demo = True
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        app.accept_report(r)
        assert app.query("#storage-map"), "No Status selection client exists"
        await pilot.press("a")
        assert app.selected == {c.id for c in r.scan.candidates[:5]}
        await pilot.press("d")
        assert app.screen.id == "confirm-cleanup" and app.focused.id == "no"
        await pilot.press("enter")
        assert app.stage == "status" and app.report is r
        assert not (tmp_path / ".Trash").exists()


@pytest.mark.asyncio
async def test_keyboard_can_reach_unmeasured_categories_and_deep_paths(tmp_path):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        assert app.query("#storage-map"), "Need keyboard-accessible treemap"
        from jev_clean.ui.storage_map import StorageMap

        view = app.query_one(StorageMap)
        await pilot.press("down", "enter")
        assert view.current.label == "Developer"
        await pilot.press("enter")
        assert view.current.label == "Xcode"
        await pilot.press("space")
        # The focused DerivedData organizational box has no learned candidate.
        assert not app.selected
        await pilot.press("enter")
        assert view.current.label == "DerivedData"
        await pilot.press("escape")
        assert view.current.label == "Xcode"
        await pilot.press("escape", "escape")
        assert view.current.id == "disk"
        await pilot.press("escape")
        assert app.stage == "menu"
