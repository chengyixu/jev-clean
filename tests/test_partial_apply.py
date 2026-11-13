"""One changed or vanished item skips itself; it never cancels the rest of a confirmed cleanup.

Live run on 2026-11-13: 154 confirmed resources, one `.ruff_cache` vanished after the scan,
and the whole cleanup reported "0 items cleaned. 1 skipped." with the reason hidden in a log.
Every item that moves still passes every identity, manifest, activity and model check.
"""

import pytest
from cache_fixtures import declare_cache
from test_model_owned_judgment import answer
from textual.widgets import Static

from jev_clean.application import service
from jev_clean.domain.models import AuditReport, CleanupResult, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.model import LayaAdvisor
from jev_clean.infrastructure.resources import measure_resource
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.ui.app import JevCleanApp


def caches(home, *names):
    items = []
    for name in names:
        path = home / name
        declare_cache(path)
        (path / "blob").write_bytes(b"generated " + name.encode())
        items.append(
            apply_policy(measure_resource(path, home, EvidenceCollector(home), set()), answer("remove"))
        )
    return items


def remove_tree(path):
    for child in path.iterdir():
        child.unlink()
    path.rmdir()


def test_an_item_gone_before_apply_skips_itself_and_the_rest_move(tmp_path, monkeypatch, neural_boundary):
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection(caches(tmp_path, "a", "gone", "c"), home=tmp_path)
    remove_tree(tmp_path / "gone")
    result = service.execute_selection(sealed, home=tmp_path)
    assert result.moved == 2 and result.completed == 2
    assert not (tmp_path / "a").exists() and not (tmp_path / "c").exists()
    assert len(result.failed) == 1
    assert str(tmp_path / "gone") in result.failed[0] and "already gone" in result.failed[0].lower()
    restored = TrashStore(tmp_path).restore(result.batch_id)
    assert restored.moved == 2 and (tmp_path / "a/blob").read_bytes() == b"generated a"


def test_an_item_changed_before_apply_skips_itself_and_the_rest_move(tmp_path, monkeypatch, neural_boundary):
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection(caches(tmp_path, "a", "busy", "c"), home=tmp_path)
    (tmp_path / "busy/new work").write_bytes(b"written after review")
    result = service.execute_selection(sealed, home=tmp_path)
    assert result.moved == 2
    assert (tmp_path / "busy/new work").read_bytes() == b"written after review"
    assert len(result.failed) == 1 and str(tmp_path / "busy") in result.failed[0]


def test_a_new_model_answer_skips_only_that_item(tmp_path, monkeypatch, neural_boundary):
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection(caches(tmp_path, "a", "kept", "c"), home=tmp_path)
    monkeypatch.setattr(
        LayaAdvisor, "predict", lambda self, item: answer("keep" if item.path.endswith("/kept") else "remove")
    )
    result = service.execute_selection(sealed, home=tmp_path)
    assert result.moved == 2 and (tmp_path / "kept/blob").exists()
    assert len(result.failed) == 1 and "keep" in result.failed[0]


def test_an_item_gone_during_preparation_is_left_out_not_fatal(tmp_path, monkeypatch, neural_boundary):
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    items = caches(tmp_path, "a", "gone")
    remove_tree(tmp_path / "gone")
    sealed = service.prepare_selection(items, home=tmp_path)
    by_name = {item.path.rsplit("/", 1)[1]: item for item in sealed}
    assert by_name["a"].selectable and by_name["a"].manifest_digest
    assert not by_name["gone"].selectable
    assert "already gone" in by_name["gone"].execution_issue.lower()


def test_an_item_gone_at_the_trash_boundary_skips_itself(tmp_path, monkeypatch, neural_boundary):
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    sealed = service.prepare_selection(caches(tmp_path, "a", "gone"), home=tmp_path)
    assessed = service.reassess_selection(sealed, home=tmp_path)
    remove_tree(tmp_path / "gone")
    moved = TrashStore(tmp_path).move(assessed, open_paths=set())
    assert moved.moved == 1
    assert len(moved.failed) == 1 and "already gone" in moved.failed[0].lower()


def test_the_result_screen_names_every_skipped_item_and_its_reason():
    from jev_clean.ui.app import cleanup_summary

    result = CleanupResult(
        completed=2,
        moved=2,
        staged_bytes=3_000_000_000,
        batch_id="b" * 32,
        failed=[
            "/x/.ruff_cache: Already gone: deleted or moved since the scan",
            "/y/cache: Model chose keep",
        ],
    )
    text = cleanup_summary(result)
    assert "2 items cleaned" in text and "3.00 GB" in text
    assert "2 skipped" in text
    assert "/x/.ruff_cache: Already gone" in text and "/y/cache: Model chose keep" in text
    assert f"jev-clean restore {'b' * 32}" in text


async def wait_for(pilot, condition):
    for _ in range(200):
        await pilot.pause(0.05)
        if condition():
            return
    raise AssertionError("TUI never reached the expected state")


@pytest.mark.asyncio
async def test_select_all_confirm_and_a_vanished_item_never_stops_the_tui_cleanup(
    tmp_path, monkeypatch, neural_boundary
):
    """The reported run, end to end through the TUI: select all, confirm, one item vanishes."""
    items = caches(tmp_path, "a", "gone", "c")
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport(items))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(140, 45)) as pilot:
        app.mode = "clean"
        app.accept_report(report)
        await pilot.press("a", "enter")
        await wait_for(pilot, lambda: app.screen.id == "confirm-cleanup")
        assert app.screen.detail.startswith("3 items")
        remove_tree(tmp_path / "gone")
        await pilot.press("y")
        await wait_for(pilot, lambda: app.stage == "done")
        text = str(app.query_one("#summary", Static).render())
        assert "2 items cleaned" in text and "1 skipped" in text
        assert f"{tmp_path / 'gone'}: Already gone" in text and "jev-clean restore" in text
    assert not (tmp_path / "a").exists() and not (tmp_path / "c").exists()


@pytest.mark.asyncio
async def test_an_item_gone_before_confirmation_is_left_out_of_the_question(
    tmp_path, monkeypatch, neural_boundary
):
    items = caches(tmp_path, "a", "gone")
    remove_tree(tmp_path / "gone")
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    report = AuditReport(1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport(items))
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(140, 45)) as pilot:
        app.mode = "clean"
        app.accept_report(report)
        await pilot.press("a", "enter")
        await wait_for(pilot, lambda: app.screen.id == "confirm-cleanup")
        assert app.screen.detail.startswith("1 item")
        assert "1 other selected items changed or vanished" in app.screen.detail
        await pilot.press("n")
    assert (tmp_path / "a/blob").exists()
