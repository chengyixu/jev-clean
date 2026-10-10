"""Default Clean candidates and byte totals contain actual paths, not owner commands."""

from test_whole_disk_scope import Model

from jev_clean.application.resources import investigate_resources
from jev_clean.infrastructure import owner_tools


def test_owner_actions_live_in_advisories_not_default_file_plan(tmp_path, monkeypatch):
    root = tmp_path / "scope"
    cache = root / "cache"
    cache.mkdir(parents=True)
    (cache / "artifact.bin").write_bytes(b"synthetic")
    monkeypatch.setattr(
        owner_tools,
        "owner_observations",
        lambda: [
            {
                "owner": "uv",
                "path": str(cache),
                "state": "verified owner fact",
                "active": False,
                "argv": ["/installed/uv", "cache", "prune"],
            }
        ],
    )
    result = investigate_resources(
        tmp_path, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert not any(c.operation == "owner_prune" for c in result.candidates)
    assert len(result.stats["owner_advisories"]) == 1
    assert result.stats["owner_advisories"][0]["owner"] == "uv"
    assert result.stats["approved_candidate_bytes"] == 0
    assert result.stats["approved"] == 0
