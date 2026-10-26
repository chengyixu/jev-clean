"""Prevent convenient treemap rendering from fabricating accounting or approval."""

from test_status_map_contract import report

from jev_clean.domain.storage_map import storage_map


def test_descendant_in_different_namespace_does_not_double_count_parent():
    r = report()
    r.categories = None
    r.exploration["nodes"] = [
        {"path": "/Users/test/Library", "allocated_bytes": 500, "is_dir": True, "complete": True},
        {
            "path": "/Users/test/Library/Developer/Xcode",
            "allocated_bytes": 200,
            "is_dir": True,
            "complete": True,
        },
    ]
    m = storage_map(r)
    assert sum(c.allocated_bytes or 0 for c in m.children) == 500


def test_photos_type_observation_is_not_claimed_to_identify_system_photo_library():
    r = report()
    r.exploration["nodes"] = [
        {
            "path": "/Users/test/Pictures/archive.photoslibrary",
            "allocated_bytes": 200,
            "is_dir": True,
            "complete": True,
        }
    ]
    m = storage_map(r)
    photos = next(c for c in m.children if c.label == "Photos")
    assert photos.allocated_bytes == r.categories.named.get("com.apple.Photos.StorageManagementExtension")
    assert photos.children[0].basis.startswith("observed allocation;")


def test_status_json_hierarchy_carries_basis_without_changing_membership_claim():
    r = report()
    data = r.to_dict()
    assert "storage_map" in data, "Agent and TUI must share the same hierarchy and recommendation semantics"
    assert data["storage_map"]["basis"] == "recorded macOS totals + separate observed paths"
    assert data["system_data"]["category_membership"] == "unattributed"


def test_missing_candidate_still_colors_recorded_raw_model_remove():
    r = report()
    r.scan.candidates = []
    r.exploration["nodes"][0]["decision"] = {"choice": "remove"}
    m = storage_map(r)
    apps = next(c for c in m.children if c.label == "Applications")
    assert apps.children[0].recommended and not apps.children[0].candidate_id
