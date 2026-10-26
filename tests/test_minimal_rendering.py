from xml.etree import ElementTree

import pytest

from jev_clean.ui.app import JevCleanApp


def visible_text(app):
    return "".join(ElementTree.fromstring(app.export_screenshot()).itertext()).replace("\u00a0", " ")


@pytest.mark.asyncio
async def test_status_map_visible_with_long_paths_at_small_width(tmp_path, neural_boundary):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("2")
        await pilot.pause(0.4)
        for node in app.report.exploration["nodes"]:
            node["path"] += "/a-directory-name-that-is-deliberately-longer-than-the-terminal-window"
        app.render_report()
        await pilot.pause(0.1)
        for width, height in [(80, 24), (60, 20)]:
            await pilot.resize_terminal(width, height)
            await pilot.pause(0.1)
            text = visible_text(app)
            assert "System Data" in text and "Storage" in text
            assert app.query_one("#treemap").region.width > 20
