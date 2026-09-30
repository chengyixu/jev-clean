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


def test_model_review_is_not_discarded_from_private_report(tmp_path):
    path = tmp_path / "files/unknown"
    path.parent.mkdir()
    path.write_bytes(b"fixture")

    class ReviewModel(Model):
        def predict(self, item):
            return answer("review")

    report = investigate_disk(
        tmp_path, ReviewModel(), "clean", roots=[path.parent], state_dir=tmp_path / "state", open_paths=set()
    )
    assert len(report.candidates) == 1
    assert report.candidates[0].decision.choice == "review"
    assert not report.candidates[0].selectable


@pytest.mark.asyncio
async def test_review_and_unavailable_removal_are_visible_but_not_selected(tmp_path):
    review = apply_policy(replace(candidate(), id="review", path=str(tmp_path / "unknown")), answer("review"))
    unavailable = apply_policy(
        replace(candidate(), id="unavailable", path=str(tmp_path / "missing"), scan_complete=False),
        answer("remove"),
    )
    report = AuditReport(
        1, "2026-01-01T00:00:00+00:00", str(tmp_path), "clean", ScanReport([review, unavailable])
    )
    app = JevCleanApp(home=tmp_path)
    async with app.run_test() as pilot:
        app.mode = "clean"
        app.accept_report(report)
        assert app.query_one("#results", DataTable).row_count == 2
        await pilot.press("a")
        assert not app.selected
        assert "investigate" in str(app.query_one("#summary", Static).render())
