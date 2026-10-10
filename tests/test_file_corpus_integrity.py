"""Sensitive controls must not vanish from heldouts during deduplication."""

from pathlib import Path


def test_every_split_retains_mixed_and_sensitive_cache_controls(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from file_resource_corpus import build_file_corpus
    from laya_cleanup_experiment import validate_splits

    data = build_file_corpus()
    validate_splits(data)
    required = {
        "cache-media-mixed",
        "cache-source-mixed",
        "cache-credential-single",
        "cache-model-single",
        "cache-db-ambiguous",
        "personal-media",
        "personal-credentials",
    }
    for split in ["train", "dev", "final"]:
        scenarios = {r["scenario"] for r in data[split]}
        assert required <= scenarios, (split, required - scenarios)
        assert {r["label"] for r in data[split]} == {0, 1, 2}
