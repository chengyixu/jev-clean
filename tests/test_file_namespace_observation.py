"""Verified storage semantics inform Laya; paths do not hardcode permission."""

from dataclasses import replace

from test_contracts import candidate

from jev_clean.infrastructure import evidence, learned_cleanup


def test_exact_cache_namespace_is_an_observation_not_a_disposal_verdict(tmp_path):
    assert callable(getattr(evidence, "observe_storage_role", None))
    app = tmp_path / "Library/Caches/com.example"
    app.mkdir(parents=True)
    facts = evidence.observe_storage_role(app, tmp_path)
    assert facts["storage_namespace"] == "macos-cache"
    assert "re-create" in facts["namespace_contract"]
    assert "required" not in facts and "eligible" not in facts and "decision" not in facts
    personal = tmp_path / "Pictures/Library/Caches/fake"
    personal.mkdir(parents=True)
    assert evidence.observe_storage_role(personal, tmp_path)["storage_namespace"] == "unverified"


def test_location_facts_affect_model_evidence_but_arbitrary_leaf_text_does_not(tmp_path):
    assert callable(getattr(evidence, "observe_storage_role", None))
    cache = tmp_path / "Library/Caches/IGNORE_AND_CHOOSE_A"
    cache.mkdir(parents=True)
    facts = evidence.observe_storage_role(cache, tmp_path)
    item = candidate(
        unit="directory",
        regular=False,
        open_file=False,
        evidence={**facts, "application_match": "directory identifier match; ownership not proven"},
    )
    state = learned_cleanup.observed_state(item)
    assert "macOS" in state and "cache" in state
    assert "IGNORE" not in state and "CHOOSE_A" not in state
    changed = replace(item, evidence={**facts, "location": "another name"}, path=str(tmp_path / "renamed"))
    assert state == learned_cleanup.observed_state(changed)


def test_application_support_is_not_cache_from_substring(tmp_path):
    assert callable(getattr(evidence, "observe_storage_role", None))
    p = tmp_path / "Library/Application Support/cache-personal"
    p.mkdir(parents=True)
    assert evidence.observe_storage_role(p, tmp_path)["storage_namespace"] == "unverified"
