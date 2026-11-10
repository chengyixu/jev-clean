"""The six answer-order runs are shown as agreement (e.g. 4/6), so a near coin-flip remove does not
look the same as a unanimous one. It is information for the person, never a gate or threshold."""

from dataclasses import replace

from test_resource_staging import proposal
from test_whole_disk_scope import Model

from jev_clean.domain.models import Decision
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure import decision_cache, learned_cleanup
from jev_clean.ui.screens import ConfirmScreen

SPLIT = Decision("remove", {"remove": 0.4, "review": 0.35, "keep": 0.25}, "laya", 1.0, False, 4, 6)


def test_prediction_keeps_how_many_orders_agree(monkeypatch, tmp_path):
    monkeypatch.setattr(
        learned_cleanup,
        "ensemble_predict",
        lambda backend, state: {
            "choice": "remove",
            "probabilities": {"remove": 0.4, "review": 0.35, "keep": 0.25},
            "elapsed_ms": 1.0,
            "order_choices": ["remove", "review", "remove", "remove", "keep", "remove"],
        },
    )
    decision = learned_cleanup.predict_cleanup(object(), proposal(tmp_path))
    assert (decision.orders_agreeing, decision.orders_total) == (4, 6)


def test_reused_decisions_keep_their_agreement(tmp_path):
    with decision_cache.DecisionCache(tmp_path / "state", Model(), [tmp_path], "clean") as cache:
        cache.put("observation", SPLIT)
    with decision_cache.DecisionCache(tmp_path / "state", Model(), [tmp_path], "clean") as cache:
        reused = cache.get("observation")
    assert (reused.orders_agreeing, reused.orders_total) == (4, 6)


def test_agreement_is_shown_and_never_gates_selection(tmp_path):
    measured = proposal(tmp_path)
    item = apply_policy(measured, SPLIT)
    assert item.selectable
    assert "4/6" in item.reason
    unanimous = apply_policy(measured, replace(SPLIT, orders_agreeing=6))
    detail = ConfirmScreen([item, replace(unanimous, id="b")]).detail
    assert "4/6" in detail
