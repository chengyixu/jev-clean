"""The TUI never blocks its event loop, Esc stops long work, and a failed drill-in keeps the map."""

import time
from dataclasses import replace

import pytest

from jev_clean.domain.models import Cancelled
from jev_clean.ui import app as app_module
from jev_clean.ui.app import JevCleanApp


def waiting_until_cancelled(seconds=5):
    def slow(*args, cancelled, **kwargs):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            if cancelled():
                raise Cancelled("stopped")
            time.sleep(0.02)
        raise AssertionError("cancel was never observed")

    return slow


async def status_report(pilot, app):
    await pilot.press("2")
    for _ in range(50):
        await pilot.pause(0.1)
        if app.stage == "status":
            return
    raise AssertionError("demo status report did not load")


@pytest.mark.asyncio
async def test_status_map_is_built_once_per_report(tmp_path, neural_boundary, monkeypatch):
    calls = []
    real = app_module.storage_map
    monkeypatch.setattr(app_module, "storage_map", lambda report: calls.append(1) or real(report))
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await status_report(pilot, app)
        await pilot.press("/", "c", "a", "c", "h", "e")
        await pilot.press("escape", "space", "a", "n")
        await pilot.resize_terminal(90, 30)
        await pilot.pause()
        assert calls == [1]


@pytest.mark.asyncio
async def test_export_runs_off_the_event_loop_and_esc_stops_it(tmp_path, neural_boundary, monkeypatch):
    monkeypatch.setattr(app_module, "save_plan", waiting_until_cancelled())
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await status_report(pilot, app)
        report = app.report
        started = time.monotonic()
        await pilot.press("e")
        await pilot.pause(0.05)
        assert time.monotonic() - started < 0.5
        assert app.busy and app.stage == "preparing"
        await pilot.press("escape")
        await pilot.pause(0.5)
        assert not app.busy and app.stage == "status" and app.report is report


@pytest.mark.asyncio
async def test_esc_stops_selection_preparation_and_keeps_the_report(tmp_path, neural_boundary, monkeypatch):
    monkeypatch.setattr(app_module, "prepare_selection", waiting_until_cancelled())
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await status_report(pilot, app)
        report = app.report
        item = replace(next(iter(app.candidate_by_id.values())), unit="directory")
        app.selected = {item.id}
        app.start_preparing([item])
        await pilot.pause(0.1)
        assert app.stage == "preparing"
        await pilot.press("escape")
        await pilot.pause(0.5)
        assert not app.busy and app.stage == "status" and app.report is report
        assert app.selected == {item.id}


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["cancel", "fail"])
async def test_stopped_drill_in_keeps_the_parent_map(tmp_path, neural_boundary, outcome):
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await status_report(pilot, app)
        report = app.report
        nodes = len(report.exploration["nodes"])
        app.expanding = str(tmp_path / "inside")
        app.busy = True
        if outcome == "cancel":
            app.cancel_event.set()
            app.accept_report(replace(report, exploration={**report.exploration, "nodes": []}))
        else:
            app.scan_failed("disk vanished")
        await pilot.pause()
        assert app.stage == "status" and app.report is report and not app.busy
        assert len(app.report.exploration["nodes"]) == nodes and app.expanding is None
        assert "Drill-in" in str(app.query_one("#summary").render())
