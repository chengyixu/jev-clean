import pytest
from test_model_owned_judgment import answer
from test_whole_disk_scope import Model

from jev_clean.application import resources
from jev_clean.domain.policy import OWNER_STORE_ISSUE
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
    assert [c.execution_issue for c in result.candidates] == [OWNER_ISSUE]
    assert not any(c.selectable for c in result.candidates)
    assert len(result.stats["owner_advisories"]) == 1


OWNER_ISSUE = "owner-managed store: only the owner-native operation is supported"


def uv_store(root, monkeypatch, target=None):
    cache = root / "cache"
    (cache / "nested").mkdir(parents=True)
    (cache / "nested/blob").write_bytes(b"fixture")
    observation = {
        "owner": "uv",
        "path": str(target or cache),
        "argv": ["/uv", "cache", "prune"],
        "state": "verified owner observation",
        "active": False,
    }
    monkeypatch.setattr(owner_tools, "owner_observations", lambda: [observation])
    return cache


@pytest.mark.parametrize("mode", ["clean", "status"])
def test_trash_move_of_an_owner_store_is_never_selectable_whatever_the_model_chose(
    tmp_path, monkeypatch, mode
):
    root = tmp_path / "scope"
    cache = uv_store(root, monkeypatch)

    class Advisor(Model):
        def predict(self, item):
            return answer("keep" if item.operation == "owner_prune" else "remove")

    result = resources.investigate_resources(
        tmp_path, Advisor(), mode, roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    trash = [c for c in result.candidates if c.path == str(cache)]
    assert trash and not trash[0].selectable
    assert trash[0].execution_issue == OWNER_ISSUE
    assert result.stats["approved"] == 0


def test_policy_blocks_trash_inside_containing_or_equal_to_an_owner_store():
    from pathlib import PurePath

    from test_model_owned_judgment import answer as decided

    from jev_clean.domain.models import Candidate, Fingerprint
    from jev_clean.domain.policy import apply_policy

    def item(path):
        return Candidate(
            id=path,
            path=path,
            allocated_bytes=1,
            age_seconds=0,
            open_file=False,
            regular=False,
            symlink=False,
            fingerprint=Fingerprint(1, 1, 1, 1, 1, 1, 1),
            kind="resource",
            unit="directory",
            scan_complete=True,
        )

    stores = [PurePath("/u/.cache/uv")]
    for path in ("/u/.cache/uv", "/u/.cache/uv/archive-v0", "/u/.cache"):
        assert apply_policy(item(path), decided("remove"), stores).execution_issue == OWNER_ISSUE
    assert apply_policy(item("/u/.cache/pip"), decided("remove"), stores).selectable


def test_preparing_an_owner_store_selection_is_refused(tmp_path, monkeypatch, neural_boundary):
    from dataclasses import replace

    from test_resource_staging import proposal

    from jev_clean.application import service

    item = proposal(tmp_path)
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    monkeypatch.setattr(
        owner_tools,
        "owner_observations",
        lambda: [{"owner": "uv", "path": str(tmp_path / "cache"), "argv": [], "state": "", "active": False}],
    )
    (sealed,) = service.prepare_selection([replace(item)], home=tmp_path)
    assert not sealed.selectable and sealed.execution_issue == OWNER_STORE_ISSUE
    result = service.execute_selection([sealed], home=tmp_path)
    assert result.moved == 0 and (tmp_path / "cache/nested/blob").exists()
