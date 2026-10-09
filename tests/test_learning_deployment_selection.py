"""Choose checkpoints on development data; failed raw holdouts cannot be called fixed."""

from test_cleanup_learning_contract import experiment_module


def test_checkpoint_selection_ignores_final_holdout_scores():
    m = experiment_module()
    candidates = [
        {"seed": 0, "dev": {"false_remove": 0, "correct": 8}, "final": {"false_remove": 4, "correct": 15}},
        {"seed": 1, "dev": {"false_remove": 1, "correct": 12}, "final": {"false_remove": 0, "correct": 24}},
    ]
    assert callable(getattr(m, "development_candidate", None))
    assert m.development_candidate(candidates)["seed"] == 0
    candidates[1]["final"] = {"false_remove": 0, "correct": 10000}
    assert m.development_candidate(candidates)["seed"] == 0


def test_final_false_removal_rejects_candidate_without_changing_raw_metrics():
    m = experiment_module()
    baseline = {"cases": 24, "correct": 22, "false_remove": 2, "removal_recall": 1.0}
    candidate = {"cases": 24, "correct": 23, "false_remove": 1, "removal_recall": 1.0}
    assert callable(getattr(m, "deployment_assessment", None))
    report = m.deployment_assessment(baseline, candidate)
    assert report["eligible_for_further_validation"] is False
    assert candidate["false_remove"] == 1


def test_keep_everything_is_not_a_successful_model_improvement():
    m = experiment_module()
    baseline = {"cases": 24, "correct": 22, "false_remove": 2, "removal_recall": 1.0}
    candidate = {"cases": 24, "correct": 16, "false_remove": 0, "removal_recall": 0.0}
    assert callable(getattr(m, "deployment_assessment", None))
    assert not m.deployment_assessment(baseline, candidate)["eligible_for_further_validation"]
