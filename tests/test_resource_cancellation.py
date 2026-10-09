from test_model_owned_judgment import answer
from test_whole_disk_scope import Model

from jev_clean.application.resources import investigate_resources


def test_cancelled_engine_does_not_return_selectable_partial_plan(tmp_path):
    root = tmp_path / "scope"
    root.mkdir()
    (root / "cache").mkdir()
    (root / "cache/blob").write_bytes(b"fixture")
    stopped = False

    class CancelModel(Model):
        def predict(self, item):
            nonlocal stopped
            stopped = True
            return answer("remove")

    result = investigate_resources(
        tmp_path,
        CancelModel(),
        "clean",
        roots=[root],
        state_dir=tmp_path / "state",
        open_paths=set(),
        cancelled=lambda: stopped,
    )
    assert not result.stats["walk_finished"]
    assert result.candidates
    assert not any(c.selectable for c in result.candidates)
