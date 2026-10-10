"""Allocation is display/reclaim evidence, not a garbage classifier or redundant GPU key."""

from dataclasses import replace

from test_contracts import candidate

from jev_clean.infrastructure.model import state_for


def test_same_semantic_observations_different_sizes_reuse_exact_model_input():
    item = candidate(
        disposal=None,
        unit="directory",
        regular=False,
        evidence={
            "file_extensions": ".jpg:2",
            "sampled_entries": "2",
            "observation_scope": "all immediate entries; descendants uninspected",
        },
    )
    changed = replace(item, allocated_bytes=123456789012, age_seconds=800 * 86400)
    assert state_for(item) == state_for(changed)


def test_size_optimization_does_not_erase_structural_or_active_evidence():
    item = candidate(
        disposal=None,
        unit="directory",
        regular=False,
        evidence={"file_extensions": ".jpg:2", "sampled_entries": "2"},
    )
    changed = replace(item, open_file=True, evidence={"file_extensions": ".sqlite:2", "sampled_entries": "2"})
    assert state_for(item) != state_for(changed)
