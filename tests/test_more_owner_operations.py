"""Owner cache facts are discovered, modeled and executed via fixed native interfaces."""

from jev_clean.infrastructure import owner_tools


def test_go_operation_is_build_cache_only_not_source_or_module_cache(tmp_path):
    root = tmp_path / "go-build"
    root.mkdir()
    calls = []

    def run(argv):
        calls.append(argv)
        if argv[1:] == ["env", "GOCACHE"]:
            return 0, str(root) + "\n", ""
        if argv[1:] == ["help", "clean"]:
            return 0, "The -cache flag causes clean to remove the entire go build cache.", ""
        return 1, "", "unsupported"

    rows = owner_tools.owner_observations({"go": "/installed/go"}, run=run, active=lambda _: False)
    assert len(rows) == 1
    assert rows[0]["argv"] == ["/installed/go", "clean", "-cache"]
    assert "modcache" not in rows[0]["argv"] and "--force" not in rows[0]["argv"]
    assert rows[0]["path"] == str(root)
    assert not any(c[1:] == ["clean", "-cache"] for c in calls)


def test_pip_cache_operation_is_owner_purge_not_arbitrary_folder_delete(tmp_path):
    root = tmp_path / "pip-cache"
    root.mkdir()
    calls = []

    def run(argv):
        calls.append(argv)
        if argv[1:] == ["cache", "dir"]:
            return 0, str(root) + "\n", ""
        if argv[1:] == ["cache", "--help"]:
            return 0, "Inspect and manage pip's wheel cache. - purge: Remove all items from the cache.", ""
        return 1, "", "unsupported"

    rows = owner_tools.owner_observations({"pip": "/installed/pip3"}, run=run, active=lambda _: False)
    assert len(rows) == 1 and rows[0]["argv"] == ["/installed/pip3", "cache", "purge"]
    assert rows[0]["path"] == str(root)
    assert all(c[-1] != "purge" for c in calls)


def test_npm_operation_is_verify_garbage_collection_not_force_clean(tmp_path):
    root = tmp_path / "npm-cache"
    root.mkdir()
    calls = []

    def run(argv):
        calls.append(argv)
        if argv[1:] == ["config", "get", "cache"]:
            return 0, str(root) + "\n", ""
        if argv[1:] == ["cache", "--help"]:
            return 0, "Manipulates packages and npx cache\nnpm cache verify", ""
        return 1, "", "unsupported"

    rows = owner_tools.owner_observations({"npm": "/installed/npm"}, run=run, active=lambda _: False)
    assert len(rows) == 1 and rows[0]["argv"] == ["/installed/npm", "cache", "verify"]
    assert rows[0]["path"] == str(root)
    assert "clean" not in rows[0]["argv"] and "--force" not in rows[0]["argv"]
    assert "unneeded" in rows[0]["state"] and "integrity" in rows[0]["state"]
