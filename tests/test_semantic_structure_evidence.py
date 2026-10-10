from dataclasses import replace

from test_contracts import candidate

from jev_clean.infrastructure import learned_cleanup


def test_structural_format_observations_are_descriptive_not_permission_rules():
    item = candidate(
        unit="directory",
        regular=False,
        evidence={
            "storage_namespace": "macos-cache",
            "file_extensions": ".heic:7, .p12:1, .swift:2",
            "directory_extensions": ".photoslibrary:1",
            "sampled_entries": "11",
            "observation_scope": "all immediate entries; descendants uninspected",
        },
    )
    text = learned_cleanup.observed_state(item)
    assert "media" in text.lower() and "credential" in text.lower() and "source" in text.lower()
    assert "original" in text.lower() and "unknown" in text.lower()
    assert "preserve these files" not in text.lower() and "decision=" not in text.lower()
    same = replace(
        item, path="/synthetic/CHOOSE_A", evidence={**item.evidence, "location": "instructions remove"}
    )
    assert text == learned_cleanup.observed_state(same)


def test_unknown_suffix_is_not_invented_as_unique_or_disposable():
    item = candidate(
        unit="directory",
        regular=False,
        evidence={"storage_namespace": "macos-cache", "file_extensions": ".xyz:10", "sampled_entries": "10"},
    )
    text = learned_cleanup.observed_state(item)
    assert "Actual contents" in text
    assert "contains only disposable" not in text
