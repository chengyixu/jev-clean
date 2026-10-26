from dataclasses import replace

import pytest
from test_status_map_contract import item, report
from textual.widgets import Static

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_expansion_at_nested_mouse_target_immediately_opens_requested_leaf(tmp_path):
    from jev_clean.ui.storage_map import StorageMap

    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        r = report()
        app.accept_report(r)
        view = app.query_one(StorageMap)
        developer = next(c for c in view.current.children if c.label == "Developer")
        view.open_entry(developer)
        # Simulate a click on a nested preview leaf before its read-only inventory returns.
        app.expanding = "/Users/test/Library/Developer/Xcode/DerivedData/one"
        child = app.expanding + "/child"
        app.accept_report(
            replace(
                r,
                scan=replace(r.scan, candidates=[item(child)]),
                exploration={
                    "nodes": [{"path": child, "allocated_bytes": 100, "is_dir": False, "complete": True}],
                    "complete": True,
                },
            )
        )
        await pilot.pause()
        assert view.current.path == "/Users/test/Library/Developer/Xcode/DerivedData/one"
        assert view.current.children[0].path == child


@pytest.mark.asyncio
async def test_native_category_root_summary_has_recorded_time(tmp_path):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)):
        app.mode = "status"
        app.accept_report(report())
        assert "09:00:00" in str(app.query_one("#summary", Static).render()), (
            "Historical native totals must not appear instantaneous"
        )


@pytest.mark.asyncio
async def test_empty_expansion_remains_a_measured_empty_directory_not_stale_size(tmp_path):
    from jev_clean.application.service import merge_status
    from jev_clean.domain.storage_map import storage_map

    old = report()
    parent = "/Applications/Editor.app"
    new = replace(
        old,
        scan=replace(old.scan, candidates=[replace(item(parent), allocated_bytes=0)]),
        exploration={
            "nodes": [{"path": parent, "allocated_bytes": 0, "is_dir": True, "complete": True}],
            "complete": True,
        },
    )
    merged = merge_status(old, new, parent)
    apps = next(c for c in storage_map(merged).children if c.label == "Applications")
    assert apps.children[0].allocated_bytes == 0 and not apps.children[0].children
    assert merged.scan.candidates[-1].allocated_bytes == 0
