import os

import pytest
from test_whole_disk_scope import Model

from jev_clean.infrastructure.decision_cache import DecisionCache


def test_decision_cache_refuses_hardlinked_database(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    outside = tmp_path / "important"
    outside.write_bytes(b"keep")
    os.link(outside, state / "decisions.sqlite3")
    with pytest.raises(ValueError):
        DecisionCache(state, Model(), [tmp_path / "root"], "clean")
    assert outside.read_bytes() == b"keep"


def test_fresh_and_reused_counts_sum_to_every_model_assessed_file(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "data"
    root.mkdir()
    for i in range(100):
        (root / str(i)).write_bytes(b"x")
    result = investigate_disk(
        home, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    s = result.stats
    assert s["fresh_model_inferences"] + s["reused_model_decisions"] == s["model_assessed_files"] == 100
    assert s["execution_unavailable"] == 0
    assert s["model_remove"] == len(result.candidates) == 100


def test_partial_observed_bytes_can_have_honest_shares():
    from jev_clean.domain.usage import usage_rows

    rows = usage_rows(
        [
            {"path": "/a", "allocated_bytes": 60, "complete": False, "is_dir": True},
            {"path": "/b", "allocated_bytes": 40, "complete": True, "is_dir": True},
        ],
        observed_basis=True,
    )
    assert {r.path: r.percent for r in rows} == {"/a": 60.0, "/b": 40.0}
    assert not rows[0].complete
