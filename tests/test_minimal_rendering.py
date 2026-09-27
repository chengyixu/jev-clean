import pytest

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_status_percent_visible_with_long_paths_at_small_width(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("2")
        await pilot.pause(0.4)
        for node in app.report.exploration["nodes"]:
            node["path"] += "/a-directory-name-that-is-deliberately-longer-than-the-terminal-window"
        app.render_report()
        await pilot.pause(0.1)
        svg = app.export_screenshot()
        assert "42%" in svg or "37%" in svg
        await pilot.resize_terminal(60, 20)
        await pilot.pause(0.2)
        svg = app.export_screenshot()
        assert "42%" in svg or "37%" in svg
