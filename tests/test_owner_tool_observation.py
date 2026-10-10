"""Supported operations are observed from the actual owner tool, never guessed by name."""

import importlib.util
from pathlib import Path


def observer():
    path = Path(__file__).resolve().parents[1] / "scripts/laya_tool_observation.py"
    assert path.exists(), "Owner-tool observation adapter missing"
    spec = importlib.util.spec_from_file_location("tool_observation", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_native_cleanup_targets_actual_cli_reported_path_without_running_prune(tmp_path):
    m = observer()
    root = tmp_path / "custom-cache"
    root.mkdir()
    calls = []

    def run(argv):
        calls.append(argv)
        if argv[1:] == ["cache", "dir"]:
            return 0, str(root) + "\n", ""
        if argv[1:] == ["cache", "prune", "--help"]:
            return 0, "Prune all unreachable objects from the cache\nUsage: uv cache prune [OPTIONS]", ""
        return 1, "", "unavailable"

    rows = m.owner_observations({"uv": "/installed/uv"}, run=run, active=lambda _: False)
    assert len(rows) == 1 and rows[0]["path"] == str(root)
    assert rows[0]["argv"] == ["/installed/uv", "cache", "prune"]
    assert rows[0]["operation"] == "owner_prune"
    assert "NOT" in rows[0]["state"] and "directory" in rows[0]["state"]
    assert all("prune" not in c or c[-1] == "--help" for c in calls)


def test_failed_discovery_never_invents_owner_path(tmp_path):
    m = observer()
    rows = m.owner_observations(
        {"uv": "/installed/uv"}, run=lambda _: (1, "", "failed"), active=lambda _: False
    )
    assert not rows


def test_active_owner_facts_are_preserved_for_model_not_filtered_out(tmp_path):
    m = observer()
    root = tmp_path / "cache"
    root.mkdir()

    def run(argv):
        return (
            (0, str(root) + "\n", "")
            if argv[1:] == ["cache", "dir"]
            else (0, "Prune all unreachable objects from the cache", "")
        )

    rows = m.owner_observations({"uv": "/installed/uv"}, run=run, active=lambda _: True)
    assert len(rows) == 1
    assert "active" in rows[0]["state"].lower()
    assert "eligible" not in rows[0] and "decision" not in rows[0]


def test_missing_semantic_help_is_an_unknown_not_a_verified_contract(tmp_path):
    m = observer()
    root = tmp_path / "cache"
    root.mkdir()

    def run(argv):
        return (
            (0, str(root) + "\n", "")
            if argv[1:] == ["cache", "dir"]
            else (0, "different unsupported command", "")
        )

    assert not m.owner_observations({"uv": "/installed/uv"}, run=run, active=lambda _: False)
