from jev_clean.infrastructure import owner_tools


def test_current_process_ancestry_is_not_a_conflicting_owner_job(monkeypatch):
    assert callable(getattr(owner_tools, "process_conflict", None))
    text = " 100 1 uv /opt/homebrew/bin/uv run python scan.py\n 101 100 python python scan.py\n 200 1 node node /path/pnpm.cjs install\n"
    assert owner_tools.process_conflict("uv", text, current_pid=101) is False
    assert owner_tools.process_conflict("pnpm", text, current_pid=101) is True


def test_another_uv_job_is_not_ignored_with_the_launcher(monkeypatch):
    assert callable(getattr(owner_tools, "process_conflict", None))
    text = " 100 1 uv /opt/homebrew/bin/uv run python scan.py\n 101 100 python python scan.py\n 222 1 uv /opt/homebrew/bin/uv sync\n"
    assert owner_tools.process_conflict("uv", text, current_pid=101) is True
