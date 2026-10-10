from test_encoder_learning_contract import module


def test_false_removal_cost_uses_semantics_not_shuffled_slot():
    m = module()
    assert callable(getattr(m, "canonical_class_weights", None))
    assert m.canonical_class_weights([0, 1, 2], false_remove_cost=3.0) == [1.0, 3.0, 3.0]
    # The same target displayed in another position must keep its semantic cost.
    order = (2, 0, 1)
    weights = m.canonical_class_weights([order[i] for i in [0, 1, 2]], false_remove_cost=3.0)
    assert weights == [3.0, 1.0, 3.0]


def test_training_epoch_budget_counts_all_option_layouts():
    m = module()
    assert callable(getattr(m, "training_budget", None))
    r = m.training_budget(cases=572, orders=6, steps=1800, batch=6)
    assert r["layout_items"] == 3432
    assert r["seen_examples"] == 10800
    assert r["effective_passes"] > 3
