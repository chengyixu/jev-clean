"""Counterfactual evidence and option shuffling must not leak labels into inputs."""

import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/laya_encoder_experiment.py"
    assert path.exists(), "Encoder-adaptation harness missing"
    spec = importlib.util.spec_from_file_location("encoder_experiment", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_option_permutation_remaps_targets_and_answers():
    m = module()
    for order in [(0, 1, 2), (2, 0, 1), (1, 2, 0)]:
        for label in range(3):
            index = m.target_index(label, order)
            assert order[index] == label
    with pytest.raises(ValueError):
        m.target_index(1, (0, 0, 2))


def test_observation_corpus_balances_names_across_labels_and_separates_families(monkeypatch):
    m = module()
    data = m.build_corpus()
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from laya_cleanup_experiment import validate_splits

    validate_splits(data)
    assert len(data["train"]) >= 150
    for split in ("train", "dev", "final"):
        assert set(row["label"] for row in data[split]) == {0, 1, 2}
    pictures = [row for row in data["train"] if row["name"] == "Pictures"]
    assert set(row["label"] for row in pictures) == {0, 1, 2}
    assert all(
        "label=" not in row["state"] and "expected=" not in row["state"]
        for rows in data.values()
        for row in rows
    )


def test_final_includes_unknown_thin_metadata_active_cache_and_needed_download_controls():
    data = module().build_corpus()
    family_labels = {r["family"]: r["label"] for r in data["final"]}
    assert family_labels["final-opaque"] == 1
    assert family_labels["final-active-cache"] == 2
    assert family_labels["final-offline-installer"] == 2
    assert family_labels["final-disposable-thumbnails"] == 0
