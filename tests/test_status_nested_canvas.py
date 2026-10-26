import pytest
from test_status_map_contract import report

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_recorded_total_box_does_not_fill_native_area_with_estimated_children(tmp_path):
    from jev_clean.ui.storage_map import TreemapCanvas

    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(120, 40)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        await pilot.pause()
        canvas = app.query_one(TreemapCanvas)
        text = "".join(segment.text for strip in canvas._map_lines for segment in strip)
        assert "Editor.app" not in text, (
            "Native category area cannot imply its observed path estimate reconciles that total"
        )


@pytest.mark.asyncio
async def test_nested_preview_click_opens_intended_directory_and_keeps_back_chain(tmp_path):
    from jev_clean.ui.storage_map import StorageMap, TreemapCanvas

    r = report()
    r.categories = None
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(120, 40)) as pilot:
        app.mode = "status"
        app.accept_report(r)
        await pilot.pause()
        view, canvas = app.query_one(StorageMap), app.query_one(TreemapCanvas)
        assert hasattr(canvas, "hit_tiles"), "Nested preview rectangles need matching hit targets"
        target = next(t for t in canvas.hit_tiles if t.entry.label == "Xcode")
        await pilot.click(canvas, offset=(target.x, target.y))
        await pilot.pause()
        assert view.current.label == "Xcode"
        assert view.stack[-1].label == "Developer"
        await pilot.press("escape")
        assert view.current.label == "Developer"
