"""Large model-proposed resources must not be buried behind traversal-order KB rows."""

from dataclasses import replace

import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer
from test_whole_disk_scope import Model
from textual.widgets import DataTable, Static

from jev_clean.application.whole_disk import investigate_disk
from jev_clean.domain.models import AuditReport, ScanReport
from jev_clean.domain.policy import apply_policy
from jev_clean.ui.app import JevCleanApp


@pytest.mark.asyncio
async def test_review_ranks_size_without_changing_model_choices_or_autoselecting(tmp_path):
    small = apply_policy(
        replace(candidate(), id="small", path=str(tmp_path / "first"), allocated_bytes=4096), answer("remove")
    )
    large = apply_policy(
        replace(candidate(), id="large", path=str(tmp_path / "large"), allocated_bytes=2_000_000_000),
        answer("remove"),
    )
    review = apply_policy(
        replace(candidate(), id="review", path=str(tmp_path / "uncertain"), allocated_bytes=3_000_000_000),
        answer("review"),
    )
    report = AuditReport(
        1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport([small, large, review])
    )
    app = JevCleanApp(home=tmp_path)
    async with app.run_test() as pilot:
        app.mode = "clean"
        app.accept_report(report)
        table = app.query_one("#results", DataTable)
        ids = [str(table.coordinate_to_cell_key((i, 0)).row_key.value) for i in range(table.row_count)]
        assert ids == ["review", "large", "small"]
        assert not app.selected
        assert "2.00 GB proposed" in str(app.query_one("#summary", Static).render())
        await pilot.press("a")
        assert app.selected == {"large", "small"}
        assert review.decision.choice == "review" and not review.selectable


def test_pipeline_report_orders_candidates_and_reports_proposed_bytes(tmp_path, monkeypatch):
    root = tmp_path / "files"
    root.mkdir()
    small = root / "small"
    large = root / "large"
    small.write_bytes(b"x")
    large.write_bytes(b"x" * 32768)
    from jev_clean.application import whole_disk
    from jev_clean.infrastructure.disk_walk import FileMeta, WalkEntry

    # Explicitly emit small first; no reliance on the filesystem's enumeration order.
    entries = [WalkEntry(p, FileMeta.from_stat(p.stat())) for p in (small, large)]
    monkeypatch.setattr(whole_disk, "walk_user", lambda *args, **kwargs: iter(entries))
    progress = []
    report = investigate_disk(
        tmp_path,
        Model(),
        "clean",
        roots=[root],
        state_dir=tmp_path / "state",
        open_paths=set(),
        progress=progress.append,
    )
    assert [c.path for c in report.candidates] == [str(large), str(small)]
    assert (
        report.stats["approved_candidate_bytes"]
        == large.stat().st_blocks * 512 + small.stat().st_blocks * 512
    )
    assert report.stats["review_candidate_bytes"] == 0
