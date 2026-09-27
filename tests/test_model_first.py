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


def test_model_controls_explorer_not_static_directory_priority(tmp_path):
    from jev_clean.application.exploration import explore
    from jev_clean.domain.models import DiskNode

    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "do-not-inspect").write_text("left")
    (right / "inspect-this").write_text("right")

    class Advisor:
        def classify(self, node):
            return Decision("data", {"data": 1.0}, "test-model-boundary", 1)

        def inspect(self, node, mode):
            choice = "inspect" if node.path == str(right) else "skip"
            return Decision(
                choice,
                {"inspect": 1.0 if choice == "inspect" else 0.0, "skip": 0.0 if choice == "inspect" else 1.0},
                "test-model-boundary",
                1,
            )

    result = explore(
        [DiskNode(str(left), 4096, True, 0), DiskNode(str(right), 4096, True, 0)],
        Advisor(),
        "status",
        max_nodes=4,
    )
    assert str(right / "inspect-this") in {n.path for n in result.nodes}
    assert str(left / "do-not-inspect") not in {n.path for n in result.nodes}
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
