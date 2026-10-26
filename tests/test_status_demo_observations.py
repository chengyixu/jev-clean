"""Public Status screenshots use synthetic observations with actual local inference."""

from test_status_map_contract import LABELS

from jev_clean.application.service import audit
from jev_clean.domain.storage_map import storage_map


def test_status_demo_has_all_ten_category_totals_and_observed_cache_context(tmp_path, neural_boundary):
    r = audit(tmp_path, "status", demo=True)
    m = storage_map(r)
    assert tuple(c.label for c in m.children[:10]) == LABELS
    assert all(c.allocated_bytes and c.allocated_bytes > 0 for c in m.children[:10]), (
        "Synthetic demo should exercise all requested categories"
    )
    caches = [
        c
        for c in r.scan.candidates
        if c.unit == "directory" and c.evidence.get("storage_namespace") == "macos-cache"
    ]
    assert caches and caches[0].evidence.get("sampled_entries"), (
        "Demo must use actual runtime-shaped descriptive observations, not invented canned verdicts"
    )
    assert r.demo and all(c.decision.backend == "test neural boundary" for c in r.scan.candidates)
