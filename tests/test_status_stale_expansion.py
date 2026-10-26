from dataclasses import replace

from test_status_map_contract import item, report

from jev_clean.application.service import merge_status
from jev_clean.domain.storage_map import storage_map


def test_new_child_inventory_does_not_reuse_stale_parent_allocation():
    old = report()
    new = replace(
        old,
        scan=replace(old.scan, candidates=[item("/Applications/Editor.app/cache")]),
        exploration={
            "nodes": [
                {
                    "path": "/Applications/Editor.app/cache",
                    "allocated_bytes": 300,
                    "is_dir": True,
                    "complete": True,
                }
            ],
            "complete": True,
        },
    )
    merged = merge_status(old, new, "/Applications/Editor.app")
    apps = next(c for c in storage_map(merged).children if c.label == "Applications")
    assert apps.children[0].allocated_bytes == 300, (
        "Old 200-byte parent is not a current child-inventory total"
    )
    assert merged.exploration["drilldowns"][-1]["prior_parent"]["allocated_bytes"] == 200


def test_parent_recommendation_marker_distinguishes_contents_from_whole_directory():
    m = storage_map(report())
    apps = next(c for c in m.children if c.label == "Applications")
    assert not apps.recommended, "Laya did not classify the category container as disposable"
    assert apps.contains_recommendations
    assert apps.children[0].recommended
