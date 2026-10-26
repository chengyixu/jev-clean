import pytest
from test_status_map_contract import report

from jev_clean.domain.models import human_bytes
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_partial_path_coverage_does_not_mark_native_total_as_lower_bound(tmp_path):
    from jev_clean.ui.storage_map import StorageMap, TreemapCanvas

    r = report()
    r.exploration["nodes"][0]["complete"] = False
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(120, 40)) as pilot:
        app.mode = "status"
        app.accept_report(r)
        await pilot.pause()
        canvas = app.query_one(TreemapCanvas)
        text = "".join(segment.text for strip in canvas._map_lines for segment in strip)
        assert "400 B+" not in text, (
            "Partial path coverage does not turn the recorded 400-byte native total into a lower bound"
        )
        view = app.query_one(StorageMap)
        view.open_entry(next(e for e in view.current.children if e.label == "Applications"))
        await pilot.pause()
        text = "".join(segment.text for strip in canvas._map_lines for segment in strip)
        assert human_bytes(200) + "+" in text, (
            "Incomplete observed path allocation must retain its partial marker"
        )
