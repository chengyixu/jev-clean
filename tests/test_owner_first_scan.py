from test_model_owned_judgment import answer
from test_whole_disk_scope import Model

from jev_clean.application import resources
from jev_clean.infrastructure import owner_tools


def test_owner_actions_assessed_before_opaque_tree_measurements(tmp_path, monkeypatch):
    root = tmp_path / "scope"
    cache = root / "cache"
    cache.mkdir(parents=True)
    (cache / "blob").write_bytes(b"fixture")
    observation = {
        "owner": "uv",
        "path": str(cache),
        "argv": ["/uv", "cache", "prune"],
        "state": "verified owner observation",
        "active": False,
    }
    monkeypatch.setattr(owner_tools, "owner_observations", lambda: [observation])
    seen = []

    class Advisor(Model):
        def predict(self, item):
            seen.append(item.operation)
            return answer("remove" if item.operation == "owner_prune" else "review")

    result = resources.investigate_resources(
        tmp_path, Advisor(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert seen[0] == "owner_prune"
    assert result.stats["owner_actions_assessed"] == 1
    assert result.stats["resources_measured"] == 1
    assert [c.operation for c in result.candidates] == ["owner_prune"]
