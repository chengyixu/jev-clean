"""Learning experiments cannot report permission gates or leaked variants as model accuracy."""

import importlib.util
from pathlib import Path

import pytest


def experiment_module():
    path = Path(__file__).resolve().parents[1] / "scripts/laya_cleanup_experiment.py"
    assert path.exists(), "Durable Laya learning/evaluation harness is missing"
    spec = importlib.util.spec_from_file_location("cleanup_experiment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_split_rejects_semantic_family_leakage():
    m = experiment_module()
    with pytest.raises(ValueError, match="family"):
        m.validate_splits(
            {
                "train": [{"family": "photos", "state": "A", "label": 2}],
                "test": [{"family": "photos", "state": "B", "label": 2}],
            }
        )


def test_split_rejects_text_leakage_even_if_family_renamed():
    m = experiment_module()
    with pytest.raises(ValueError, match="text"):
        m.validate_splits(
            {
                "train": [{"family": "a", "state": "same text", "label": 2}],
                "test": [{"family": "b", "state": "same text", "label": 2}],
            }
        )


def test_raw_metrics_count_false_remove_even_without_execution_permission():
    m = experiment_module()
    result = m.metrics([2, 1, 0, 0], [0, 1, 0, 2])
    assert result["correct"] == 2
    assert result["false_remove"] == 1
    assert result["removal_recall"] == 0.5


def test_authored_corpus_holdout_is_family_disjoint_and_has_all_classes():
    m = experiment_module()
    corpus = m.corpus()
    m.validate_splits(corpus)
    for split in ("train", "dev", "test"):
        assert set(row["label"] for row in corpus[split]) == {0, 1, 2}
    assert len(corpus["test"]) >= 18


def test_head_final_corpus_preserves_frozen_cases_and_disjoint_families(monkeypatch):
    directory = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(directory))
    import laya_cleanup_head_experiment as head

    data = head.head_corpus()
    experiment_module().validate_splits(data)
    assert len(data["final"]) == 24
    assert set(row["label"] for row in data["final"]) == {0, 1, 2}
    names = {row["family"]: row["label"] for row in data["final"]}
    assert names["retained-installer"] == 2
    assert names["active-cache"] == 2
    assert names["unneeded-compiler"] == 0
    # Native runtime imports are lazy: inspecting splits never downloads/loads weights.
    assert "mlx" not in head.__dict__
