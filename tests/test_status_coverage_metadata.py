from test_status_map_contract import report

from jev_clean.domain.storage_map import storage_map


def test_partial_disk_access_is_retained_in_shared_map_contract():
    r = report()
    r.coverage = {"complete": False, "scope_finished": True, "resources_measured": 4}
    r.exploration["complete"] = False
    assert not storage_map(r).complete, (
        "A rendered map must not imply full access just because measured blocks exist"
    )
    assert not r.to_dict()["storage_map"]["complete"]
