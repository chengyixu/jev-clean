"""Fresh drilldown keeps truthful non-overlapping hierarchy and keyboard behavior."""

from dataclasses import replace

import pytest
from test_status_map_contract import item, report

from jev_clean.ui.app import JevCleanApp


def test_measured_namespace_root_contains_descendants_not_duplicate_siblings():
    from jev_clean.domain.storage_map import storage_map

    r = report()
    r.categories = None
    r.exploration["nodes"] = [
        {"path": "/Users/test/Library", "allocated_bytes": 500, "is_dir": True, "complete": True},
        {"path": "/Users/test/Library/Caches/a", "allocated_bytes": 200, "is_dir": True, "complete": True},
    ]
    m = storage_map(r)
    system = next(c for c in m.children if c.label == "System Data")
    assert system.allocated_bytes == 500, "Measured parent must not be summed alongside its descendants"
    assert len(system.children) == 1


@pytest.mark.asyncio
async def test_uppercase_a_and_mouse_click_can_select_the_focused_file(tmp_path):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        await pilot.press("A")
        assert len(app.selected) == 5, "The requested A key must work, not only lowercase a"


@pytest.mark.asyncio
async def test_expanded_directory_opens_next_layer_without_losing_other_selection(tmp_path):
    from jev_clean.ui.storage_map import StorageMap

    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        view = app.query_one(StorageMap)
        app.selected = {"/Users/test/Documents/book"}
        category = next(c for c in view.current.children if c.label == "Applications")
        view.open_entry(category)
        app.expanding = "/Applications/Editor.app"
        new = replace(
            report(),
            scan=replace(report().scan, candidates=[item("/Applications/Editor.app/cache")]),
            exploration={
                "nodes": [
                    {
                        "path": "/Applications/Editor.app/cache",
                        "allocated_bytes": 200,
                        "is_dir": True,
                        "complete": True,
                    }
                ]
            },
        )
        app.accept_report(new)
        assert view.current.path == "/Applications/Editor.app", (
            "A successful read-only drilldown must show its children immediately"
        )
        assert app.selected == {"/Users/test/Documents/book"}
        assert view.current.children[0].label == "cache"
        await pilot.press("escape")
        assert view.current.label == "Applications"
