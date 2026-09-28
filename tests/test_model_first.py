import pytest

from jev_clean.application.service import audit
from jev_clean.domain.models import Decision
from jev_clean.infrastructure.model import LayaAdvisor


def test_missing_model_stops_both_modes_before_disk_scan(monkeypatch, tmp_path):
    def fail(self):
        raise RuntimeError("Model is required: setup first")

    monkeypatch.setattr(LayaAdvisor, "load", fail)
    for mode in ("clean", "status"):
        with pytest.raises(RuntimeError, match="Model is required"):
            audit(tmp_path, mode)


def test_demo_also_requires_real_inference(monkeypatch, tmp_path):
    def fail(self):
        raise RuntimeError("No real inference")

    monkeypatch.setattr(LayaAdvisor, "load", fail)
    with pytest.raises(RuntimeError, match="No real inference"):
        audit(tmp_path, "clean", demo=True)


def test_removed_modes_are_not_accepted(tmp_path):
    for mode in ("analyze", "optimize"):
        with pytest.raises(ValueError, match="mode"):
            audit(tmp_path, mode)


def test_model_prioritizes_volumes_without_skipping_the_rest(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "do-not-inspect").write_text("left")
    (right / "inspect-this").write_text("right")

    class Advisor:
        def classify(self, node):
            return Decision("data", {"data": 1.0}, "test-model-boundary", 1)

        def choose_directory(self, nodes, mode):
            index = next((i for i, n in enumerate(nodes) if n.path == str(right)), 0)
            return Decision(
                f"n{index}",
                {f"n{i}": 1.0 if i == index else 0.0 for i in range(len(nodes))},
                "test-model-boundary",
                1,
            )

        def predict(self, item):
            return Decision("keep", {"remove": 0.0, "review": 0.0, "keep": 1.0}, "test-model-boundary", 1)

    result = investigate_disk(
        tmp_path, Advisor(), "status", roots=[left, right], state_dir=tmp_path / "state", open_paths=set()
    )
    assert result.steps[0].path == str(right)
    assert result.stats["observed_regular_files"] == result.stats["model_assessed_files"] == 2
    assert result.stats["walk_finished"]
    assert result.steps[0].decision.backend == "test-model-boundary"


def test_unassessed_candidate_is_never_selectable():
    from test_contracts import candidate

    from jev_clean.domain.policy import apply_policy

    item = apply_policy(candidate(open_file=False), None)
    assert not item.selectable
    item = apply_policy(item, Decision("keep", {"remove": 0.0, "review": 0.0, "keep": 1.0}, "model", 1))
    assert not item.selectable
    item = apply_policy(item, Decision("remove", {"remove": 0.95, "review": 0.03, "keep": 0.02}, "model", 1))
    assert item.selectable
