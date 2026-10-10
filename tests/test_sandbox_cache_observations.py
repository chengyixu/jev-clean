"""Sandbox organizational discovery keeps cache and account-state resources separate."""

from jev_clean.infrastructure.evidence import observe_storage_role
from jev_clean.infrastructure.resources import discover_resources
from jev_clean.infrastructure.volumes import DiskScope


def test_container_cache_namespace_observed_without_application_support_false_positive(tmp_path):
    cache = tmp_path / "Library/Containers/app.example/Data/Library/Caches/blob"
    cache.mkdir(parents=True)
    data = tmp_path / "Library/Containers/app.example/Data/Library/Application Support/cache-personal"
    data.mkdir(parents=True)
    assert observe_storage_role(cache, tmp_path)["storage_namespace"] == "macos-cache"
    assert observe_storage_role(data, tmp_path)["storage_namespace"] == "unverified"


def test_group_cache_namespace_observed_without_name_substring_guess(tmp_path):
    cache = tmp_path / "Library/Group Containers/group.example/Library/Caches/item"
    cache.mkdir(parents=True)
    fake = tmp_path / "Pictures/group.example/Library/Caches/item"
    fake.mkdir(parents=True)
    assert observe_storage_role(cache, tmp_path)["storage_namespace"] == "macos-cache"
    assert observe_storage_role(fake, tmp_path)["storage_namespace"] == "unverified"


def test_frontier_exposes_cache_subtrees_but_does_not_drop_account_state(tmp_path):
    cache = tmp_path / "Library/Containers/app.example/Data/Library/Caches/chunks"
    cache.mkdir(parents=True)
    (cache / "blob.bin").write_bytes(b"synthetic cache")
    state = tmp_path / "Library/Containers/app.example/Data/Library/Application Support/account"
    state.mkdir(parents=True)
    (state / "state.db").write_bytes(b"unique fixture")
    result = discover_resources(tmp_path, DiskScope([tmp_path]))
    assert cache in result.paths
    assert tmp_path / "Library/Containers/app.example/Data/Library/Application Support" in result.paths
    assert all(not a.is_relative_to(b) for a in result.paths for b in result.paths if a != b)
