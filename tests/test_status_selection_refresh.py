from dataclasses import replace

import pytest
from test_status_map_contract import item, report

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_fresh_status_judgment_revokes_stale_selection(tmp_path):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        old = report()
        app.accept_report(old)
        await pilot.press("a")
        path = "/Applications/Editor.app"
        assert path in app.selected
        new = replace(
            old,
            scan=replace(old.scan, candidates=[item(path, "review")]),
            exploration={"nodes": [{"path": path, "allocated_bytes": 200, "is_dir": True, "complete": True}]},
        )
        app.expanding = path
        app.accept_report(new)
        assert path not in app.selected, "A refreshed review/keep/unready resource must not stay selected"
        assert all(app.candidate_by_id[i].selectable for i in app.selected)
