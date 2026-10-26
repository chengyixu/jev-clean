"""Post-training data uses the unchanged production input, without path policies."""

import importlib.util
from pathlib import Path

import pytest


def experiment(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "runtime_encoder_experiment", scripts / "laya_encoder_experiment.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_corpus_retains_counterfactuals_without_new_runtime_features(monkeypatch):
    experiment(monkeypatch)
    from laya_cleanup_experiment import validate_splits
    from runtime_resource_corpus import build_runtime_corpus

    corpus = build_runtime_corpus()
    validate_splits(corpus)
    for rows in corpus.values():
        scenarios = {row["scenario"] for row in rows}
        assert {
            "declared-idle",
            "declared-active",
            "declared-unknown-activity",
            "undeclared-idle",
        } <= scenarios
        assert {
            "declared-source",
            "declared-media",
            "declared-credentials",
            "declared-model",
            "declared-database",
        } <= scenarios
        assert all("/synthetic/resource" not in row["state"] for row in rows)
        assert all("xcode-generated" not in row["state"] for row in rows)
        by_state = {}
        for row in rows:
            assert by_state.setdefault(row["state"], row["label"]) == row["label"]


def test_checkpoint_scoring_uses_the_deployed_probability_ensemble(monkeypatch):
    module = experiment(monkeypatch)
    from jev_clean.infrastructure import learned_cleanup

    calls = []

    def boundary(backend, state):
        calls.append((backend, state))
        return {"choice": "remove" if state == "declared idle" else "review"}

    monkeypatch.setattr(learned_cleanup, "ensemble_predict", boundary)
    backend = object()
    rows = [{"state": "declared idle", "label": 0}, {"state": "unknown", "label": 1}]
    score = module.native_metrics(backend, rows)
    assert score["correct"] == 2 and score["false_remove"] == 0
    assert calls == [(backend, "declared idle"), (backend, "unknown")]


def test_external_training_corpus_refuses_contradictory_observations(tmp_path, monkeypatch):
    import json

    module = experiment(monkeypatch)
    rows = {key: [{"family": key, "label": 1, "state": key}] for key in ("train", "dev", "final")}
    rows["train"].append({"family": "other", "label": 0, "state": "train"})
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match="contradictory"):
        module.load_external_corpus(path)
