import pytest
from test_status_map_contract import report

from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_category_drilldown_labels_observed_basis_not_recorded_parent_basis(tmp_path):
    from textual.widgets import Static

    from jev_clean.ui.storage_map import StorageMap

    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        app.accept_report(report())
        view = app.query_one(StorageMap)
        view.open_entry(next(e for e in view.current.children if e.label == "Applications"))
        await pilot.pause()
        text = str(app.query_one("#summary", Static).render())
        assert "observed allocation" in text.lower() and "estimated" in text.lower()
        assert "recorded macOS total" not in text


@pytest.mark.asyncio
async def test_clicking_raw_recommended_file_toggles_selection_without_deleting(tmp_path):
    from jev_clean.ui.storage_map import StorageMap

    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(100, 32)) as pilot:
        app.mode = "status"
        r = report()
        r.exploration["nodes"][0]["is_dir"] = False
        app.accept_report(r)
        view = app.query_one(StorageMap)
        view.open_entry(next(e for e in view.current.children if e.label == "Applications"))
        view.open_entry(view.current.children[0])
        await pilot.pause()
        assert app.selected == {"/Applications/Editor.app"}
        assert app.screen.id != "confirm-cleanup" and not (tmp_path / ".Trash").exists()


def test_builtin_app_namespace_is_macos_estimate_not_unattributed():
    from jev_clean.domain.storage_map import path_group

    assert path_group("/System/Applications/Mail.app", "/Users/test")[0] == "macOS"
