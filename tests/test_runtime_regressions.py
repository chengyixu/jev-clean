import sys

import pytest
from textual.widgets import Static

from jev_clean.domain.usage import usage_rows
from jev_clean.infrastructure import native
from jev_clean.ui.app import JevCleanApp


def test_timeout_preserves_captured_stdout_and_stderr():
    code, out, err = native.run(
        [
            sys.executable,
            "-S",  # no third-party site hooks before the fixture writes its first byte
            "-u",
            "-c",
            "import sys,time;print('4\\t/tmp/finished');print('diagnostic',file=sys.stderr);time.sleep(5)",
        ],
        timeout=1,
    )
    assert code == 124 and "4\t/tmp/finished" in out and "diagnostic" in err


def test_directory_measurement_keeps_children_and_partial_lower_bound():
    rows = native.parse_du_tree("/fixture", 124, "4\t/fixture/a\n8\t/fixture/b\n", "Timeout")
    by = {r.path: r for r in rows}
    assert by["/fixture"].allocated_bytes == 12288 and not by["/fixture"].complete
    assert by["/fixture/a"].allocated_bytes == 4096 and by["/fixture/a"].complete


def test_one_permission_error_does_not_invalidate_other_subtrees():
    rows = native.parse_du_tree(
        "/fixture",
        1,
        "4\t/fixture/a\n8\t/fixture/b\n12\t/fixture\n",
        "du: /fixture/b/private: Permission denied\n",
    )
    by = {r.path: r for r in rows}
    assert by["/fixture/a"].complete
    assert not by["/fixture/b"].complete and not by["/fixture"].complete


def test_unknown_ancestor_does_not_mask_measured_children():
    rows = usage_rows(
        [
            {"path": "/home", "allocated_bytes": None, "complete": False, "is_dir": True},
            {"path": "/home/a", "allocated_bytes": 500, "complete": True, "is_dir": True},
            {"path": "/home/b", "allocated_bytes": 500, "complete": True, "is_dir": True},
        ]
    )
    by = {r.path: r.percent for r in rows}
    assert by["/home/a"] == 50 and by["/home/b"] == 50


@pytest.mark.asyncio
async def test_sudo_question_left_right_then_enter(tmp_path, neural_boundary, monkeypatch):
    app = JevCleanApp(home=tmp_path)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("1")
        assert app.focused.id == "no"
        await pilot.press("left")
        assert app.focused.id == "yes"
        await pilot.press("right")
        assert app.focused.id == "no"
        await pilot.press("escape")
        assert not app.busy


@pytest.mark.asyncio
async def test_zero_assessed_is_not_presented_as_clean_disk(tmp_path, neural_boundary):
    from jev_clean.application.service import audit

    report = audit(tmp_path, "clean", demo=True)
    report.scan.candidates = []
    report.scan.files_seen = 0
    report.exploration["complete"] = False
    app = JevCleanApp(home=tmp_path, demo=True)
    async with app.run_test(size=(80, 24)):
        app.mode = "clean"
        app.accept_report(report)
        text = str(app.query_one("#summary", Static).render())
        assert "Nothing to clean" not in text and (
            "incomplete" in text.lower() or "not assessed" in text.lower()
        )
