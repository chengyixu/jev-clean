"""Post-training data is rendered by the production observation API, without path policies."""

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


def test_every_verified_role_has_matched_activity_and_personal_format_counterfactuals(monkeypatch):
    experiment(monkeypatch)
    from runtime_resource_corpus import ROLE_IDLE_LABEL, build_runtime_corpus

    from jev_clean.infrastructure.evidence import STORAGE_ROLES

    assert set(ROLE_IDLE_LABEL) == set(STORAGE_ROLES) - {"macos-cache", "macos-diagnostic-log"}
    for split, rows in build_runtime_corpus().items():
        for role, (label, contract) in STORAGE_ROLES.items():
            if role not in ROLE_IDLE_LABEL:
                continue
            mine = [r for r in rows if f"Actual filesystem namespace: {label}. {contract}" in r["state"]]
            by = {r["scenario"]: r["label"] for r in mine}
            assert by["role-active"] == 2, (split, role)
            assert by["role-idle"] == ROLE_IDLE_LABEL[role], (split, role)
            assert by["role-unknown-activity"] != 0, (split, role)
            if ROLE_IDLE_LABEL[role] == 0:
                personal = [r for r in mine if r["scenario"].startswith("role-personal-")]
                assert len(personal) >= 5 and all(r["label"] == 1 for r in personal)
        repository = [r for r in rows if r["scenario"] == "cache-personal-repository"]
        assert repository and "source or repository formats" in repository[0]["state"]
