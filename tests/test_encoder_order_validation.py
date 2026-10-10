"""Development selection must exercise the same reordered layouts as robustness tests."""

from test_encoder_learning_contract import module


def test_development_orders_include_all_permutations_without_using_final_labels():
    m = module()
    assert callable(getattr(m, "evaluation_orders", None))
    orders = m.evaluation_orders("dev", robustness=True)
    assert set(orders) == {(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)}
    assert m.evaluation_orders("final", robustness=False) == [(0, 1, 2)]


def test_expanded_corpus_is_family_disjoint_and_retains_unknown_controls(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from laya_cleanup_experiment import validate_splits

    m = module()
    rows = m.build_corpus(extra_training=True)
    validate_splits(rows)
    assert len(rows["train"]) == 300
    assert set(r["label"] for r in rows["train"] if r["name"] == "Pictures") == {0, 1, 2}
